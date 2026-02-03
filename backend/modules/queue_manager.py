import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / "config" / ".env"
load_dotenv(ENV_PATH)

QUEUE_FILE = BASE_DIR / "data_cache" / "pending_posts.json"
BUFFER_EMAIL = os.getenv("BUFFER_EMAIL")
BUFFER_PASSWORD = os.getenv("BUFFER_PASSWORD")
BUFFER_COOKIES_PATH = os.getenv("BUFFER_COOKIES_PATH")
BUFFER_MAX_QUEUE = int(os.getenv("BUFFER_MAX_QUEUE", "10"))
BUFFER_HEADLESS = os.getenv("BUFFER_HEADLESS", "true").lower() == "true"


def _require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        print(f"Error: Missing required env var {var_name}.")
        print(f"-> Set it in {ENV_PATH}")
        raise SystemExit(1)
    return value


class QueueManager:
    def __init__(self):
        self.queue_data = self._load_queue()

    def _load_queue(self) -> list[dict]:
        if not QUEUE_FILE.exists():
            return []
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_queue(self) -> None:
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
        cookies_path = Path(BUFFER_COOKIES_PATH) if BUFFER_COOKIES_PATH else None
        use_cookies = bool(cookies_path and cookies_path.exists())

        if not use_cookies:
            _require_env("BUFFER_EMAIL")
            _require_env("BUFFER_PASSWORD")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=BUFFER_HEADLESS)
            context = await browser.new_context(
                storage_state=str(cookies_path) if use_cookies else None
            )
            page = await context.new_page()

            print("Logging into Buffer...")
            await page.goto("https://login.buffer.com/login", wait_until="domcontentloaded")

            if await page.locator('input[name="email"]').is_visible():
                await page.fill('input[name="email"]', BUFFER_EMAIL or "")
                await page.fill('input[name="password"]', BUFFER_PASSWORD or "")
                await page.click('button[type="submit"]')
                await page.wait_for_load_state("networkidle")

            await page.wait_for_url("**/publish/**", timeout=60000)
            print("Login successful.")

            queue_items = await page.locator("div[data-testid='queue-item']").count()
            print(f"Current Queue Count: {queue_items}/{BUFFER_MAX_QUEUE}")

            if queue_items >= BUFFER_MAX_QUEUE:
                print("Queue is full. Exiting.")
                await browser.close()
                return

            post = self.get_next_post()
            if not post:
                print("No pending posts in local queue.")
                await browser.close()
                return

            print(f"Scheduling Post: {post.get('id')}")

            await page.click("button[data-testid='composer-open-button']")
            await page.wait_for_selector("div[role='textbox']")
            await page.type("div[role='textbox']", post.get("text", ""))

            image_path = post.get("image_path")
            if image_path:
                try:
                    async with page.expect_file_chooser() as fc_info:
                        await page.click("button[aria-label='Add image or video']")
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(image_path)
                except Exception:
                    print("Image upload failed. Continuing without image.")

            await page.click("button[data-testid='composer-send-button']")
            await page.wait_for_selector("div[role='textbox']", state="hidden")
            print("Post added to Buffer queue.")

            self.mark_as_scheduled(post.get("id", ""))
            await browser.close()


if __name__ == "__main__":
    manager = QueueManager()
    asyncio.run(manager.fill_slots())
