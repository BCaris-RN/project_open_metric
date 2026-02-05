import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

from backend.modules.config_store import (
    get_buffer_email,
    get_buffer_password,
    get_buffer_cookies_path,
)

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / "config" / ".env"
load_dotenv(ENV_PATH)

QUEUE_FILE = BASE_DIR / "data_cache" / "pending_posts.json"
BUFFER_MAX_QUEUE = int(os.getenv("BUFFER_MAX_QUEUE", "10"))
BUFFER_HEADLESS = os.getenv("BUFFER_HEADLESS", "true").lower() == "true"

logger = logging.getLogger("open_metric.queue")


def _require_value(label: str, value: str | None) -> str:
    if not value:
        logger.error("Missing required value for %s. Configure it via Settings.", label)
        raise SystemExit(1)
    return value


async def _retry(action, label: str, attempts: int = 3, delay: float = 1.0):
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


class QueueManager:
    def __init__(self):
        self.queue_data = self._load_queue()

    def _load_queue(self) -> list[dict]:
        if not QUEUE_FILE.exists():
            return []
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_queue(self) -> None:
        QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.queue_data, f, indent=2)

    def get_next_post(self) -> dict | None:
        """Finds the first post with status 'pending'."""
        for post in self.queue_data:
            if post.get("status") == "pending":
                return post
        return None

    def mark_as_scheduled(self, post_id: str) -> None:
        for post in self.queue_data:
            if post.get("id") == post_id:
                post["status"] = "scheduled"
                break
        self._save_queue()

    async def fill_slots(self) -> None:
        cookies_path = Path(get_buffer_cookies_path())
        use_cookies = cookies_path.exists()

        buffer_email = get_buffer_email()
        buffer_password = get_buffer_password()

        if not use_cookies:
            _require_value("buffer_email", buffer_email)
            _require_value("buffer_password", buffer_password)

        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=BUFFER_HEADLESS)
                context = await browser.new_context(
                    storage_state=str(cookies_path) if use_cookies else None
                )
                page = await context.new_page()

                logger.info("Logging into Buffer...")
                await _retry(
                    lambda: page.goto(
                        "https://login.buffer.com/login", wait_until="domcontentloaded"
                    ),
                    "Buffer login page",
                )

                if await page.locator('input[name="email"]').is_visible():
                    await page.fill('input[name="email"]', buffer_email or "")
                    await page.fill('input[name="password"]', buffer_password or "")
                    await page.click('button[type="submit"]')
                    await page.wait_for_load_state("networkidle")

                await _retry(
                    lambda: page.wait_for_url("**/publish/**", timeout=60000),
                    "Buffer publish URL",
                )
                logger.info("Login successful.")

                queue_items = await page.locator("div[data-testid='queue-item']").count()
                logger.info("Current Queue Count: %s/%s", queue_items, BUFFER_MAX_QUEUE)

                if queue_items >= BUFFER_MAX_QUEUE:
                    logger.info("Queue is full. Exiting.")
                    await browser.close()
                    return

                post = self.get_next_post()
                if not post:
                    logger.info("No pending posts in local queue.")
                    await browser.close()
                    return

                logger.info("Scheduling Post: %s", post.get("id"))

                await _retry(
                    lambda: page.click("button[data-testid='composer-open-button']"),
                    "Open composer",
                )
                await _retry(
                    lambda: page.wait_for_selector("div[role='textbox']"),
                    "Composer textbox",
                )
                await page.type("div[role='textbox']", post.get("text", ""))

                image_path = post.get("image_path")
                if image_path:
                    try:
                        async with page.expect_file_chooser() as fc_info:
                            await page.click("button[aria-label='Add image or video']")
                        file_chooser = await fc_info.value
                        await file_chooser.set_files(image_path)
                    except Exception:
                        logger.warning("Image upload failed. Continuing without image.")

                await _retry(
                    lambda: page.click("button[data-testid='composer-send-button']"),
                    "Submit post",
                )
                await _retry(
                    lambda: page.wait_for_selector("div[role='textbox']", state="hidden"),
                    "Composer close",
                )
                logger.info("Post added to Buffer queue.")

                self.mark_as_scheduled(post.get("id", ""))
                await browser.close()
        finally:
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    manager = QueueManager()
    asyncio.run(manager.fill_slots())
