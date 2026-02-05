import asyncio
import hashlib
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.modules.drive_sync import DriveSync
from backend.modules.sqlite_store import SQLiteStore

ENV_PATH = BASE_DIR / "config" / ".env"
load_dotenv(ENV_PATH)

EMAIL = os.getenv("METRICOOL_EMAIL")
PASSWORD = os.getenv("METRICOOL_PASSWORD")
COOKIES_PATH = os.getenv(
    "METRICOOL_COOKIES_PATH", str(PROJECT_ROOT / "keys" / "metricool_cookies.json")
)
ANALYTICS_URL = os.getenv("METRICOOL_ANALYTICS_URL")

logger = logging.getLogger("open_metric.harvester")


def _require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        logger.error("Missing required env var %s. Set it in %s", var_name, ENV_PATH)
        raise SystemExit(1)
    return value


def _get_value(row: pd.Series, keys: list[str], default=None):
    for key in keys:
        if key in row and pd.notna(row[key]):
            return row[key]
    return default


def _parse_number(value) -> float:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    if s == "" or s.lower() in {"nan", "none", "null", "-"}:
        return 0.0

    s = s.replace("%", "")

    multiplier = 1.0
    if s[-1:] in {"K", "M", "B"}:
        suffix = s[-1:]
        s = s[:-1]
        multiplier = {"K": 1e3, "M": 1e6, "B": 1e9}.get(suffix, 1.0)

    if "," in s and "." not in s:
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")

    try:
        return float(s) * multiplier
    except ValueError:
        return 0.0


def _to_iso(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    try:
        dt = pd.to_datetime(value, utc=True, errors="coerce")
        if pd.isna(dt):
            return str(value)
        return dt.isoformat()
    except Exception:
        return str(value)


class MetricoolHarvester:
    def __init__(self):
        self.sync_engine = DriveSync()
        self.store = SQLiteStore()

    async def _retry(self, action, label: str, attempts: int = 3, delay: float = 1.0):
        last_exc = None
        for attempt in range(1, attempts + 1):
            try:
                return await action()
            except Exception as exc:
                last_exc = exc
                logger.warning("%s failed (attempt %s/%s): %s", label, attempt, attempts, exc)
                if attempt < attempts:
                    await asyncio.sleep(delay)
                    delay *= 2
        raise last_exc

    async def scrape(self):
        cookies_path = Path(COOKIES_PATH)
        use_cookies = cookies_path.exists()

        if not use_cookies:
            _require_env("METRICOOL_EMAIL")
            _require_env("METRICOOL_PASSWORD")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                storage_state=str(cookies_path) if use_cookies else None
            )
            page = await context.new_page()

            logger.info("Logging into Metricool...")
            await self._retry(
                lambda: page.goto("https://app.metricool.com/", wait_until="domcontentloaded"),
                "Metricool landing page",
            )

            if await page.locator('input[name="email"]').is_visible():
                await page.fill('input[name="email"]', EMAIL or "")
                await page.fill('input[name="password"]', PASSWORD or "")
                await page.click('button[type="submit"]')
                await page.wait_for_load_state("networkidle")

            if ANALYTICS_URL:
                await self._retry(
                    lambda: page.goto(ANALYTICS_URL, wait_until="networkidle"),
                    "Metricool analytics URL",
                )
            else:
                logger.info("Navigating to Analytics...")

                async def _open_analytics():
                    try:
                        await page.get_by_role("link", name="Analytics").click(timeout=10000)
                        return True
                    except Exception:
                        await page.click("text=Analytics", timeout=10000)
                        return True

                await self._retry(_open_analytics, "Analytics navigation")
                await page.wait_for_timeout(3000)

            async def _open_list():
                try:
                    await page.get_by_role("button", name="List").click(timeout=5000)
                    return True
                except Exception:
                    await page.click("text=List", timeout=5000)
                    return True

            await self._retry(_open_list, "List toggle")

            try:
                await self._retry(
                    lambda: page.wait_for_selector("table", timeout=30000),
                    "Metricool table",
                )
            except Exception as exc:
                logger.error("No table found after retries: %s", exc)
                await browser.close()
                return

            html = await page.content()
            dfs = pd.read_html(html)
            if not dfs:
                logger.warning("No table found in page HTML.")
                await browser.close()
                return

            raw_df = dfs[0]
            logger.info("Scraped %s rows from Metricool.", len(raw_df))

            clean_df = self.normalize_data(raw_df)
            inserted = self.store.upsert_df(clean_df)
            logger.info("SQLite insert: %s new rows", inserted)
            try:
                await asyncio.to_thread(self.sync_engine.push_update, clean_df)
            except Exception as exc:
                logger.warning("Drive sync failed: %s", exc)

            await browser.close()

    def normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        normalized = []

        for _, row in df.iterrows():
            reach = _parse_number(
                _get_value(row, ["Reach", "Alcance", "Impressions", "Impresiones"])
            )
            clicks = _parse_number(_get_value(row, ["Clicks", "Clics"]))
            interactions = _parse_number(
                _get_value(row, ["Interactions", "Interacciones", "Engagements"])
            )
            likes = _parse_number(_get_value(row, ["Likes", "Me gusta", "Like"]))
            comments = _parse_number(_get_value(row, ["Comments", "Comentarios"]))
            shares = _parse_number(
                _get_value(row, ["Shares", "Shared", "Compartidos", "Saves", "Guardados"])
            )

            if interactions == 0:
                interactions = likes + comments + shares

            engagement_score = round(interactions / reach, 4) if reach > 0 else 0

            platform = str(
                _get_value(
                    row,
                    ["Platform", "Plataforma", "Network", "Red", "Canal", "Channel"],
                    "Metricool",
                )
            )
            media_type = str(
                _get_value(row, ["Type", "Tipo", "Format", "Formato"], "Unknown")
            )
            caption = str(
                _get_value(
                    row,
                    ["Text", "Post", "Caption", "Contenido", "Descripción", "Description"],
                    "",
                )
            ).strip()
            timestamp = _to_iso(
                _get_value(
                    row, ["Date", "Fecha", "Day", "Día", "Published", "Publicado", "Time"]
                )
            )

            base_id = _get_value(row, ["Post ID", "PostId", "ID", "Id", "id", "URL", "Link", "Enlace"])
            if base_id is None or str(base_id).strip() == "" or str(base_id).lower() == "nan":
                base_id = f"{platform}|{timestamp}|{caption}|{reach}|{likes}|{comments}|{shares}"

            post_id = f"metri_{hashlib.sha1(str(base_id).encode('utf-8')).hexdigest()[:16]}"
            conversion_status = "Clicked" if clicks > 0 else "None"

            normalized.append(
                {
                    "post_id": post_id,
                    "timestamp_utc": timestamp,
                    "platform": platform,
                    "media_type": media_type,
                    "engagement_score": engagement_score,
                    "reach": reach,
                    "likes": likes,
                    "comments": comments,
                    "shares": shares,
                    "caption_text": caption,
                    "conversion_status": conversion_status,
                }
            )

        return pd.DataFrame(normalized)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    harvester = MetricoolHarvester()
    asyncio.run(harvester.scrape())
