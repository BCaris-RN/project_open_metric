from playwright.sync_api import sync_playwright
import json
import os


def save_cookies():
    print("Launching browser...")
    with sync_playwright() as p:
        # Launch Chromium with UI so login can be completed manually.
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        print("Opening Metricool. Please log in manually.")
        page.goto("https://app.metricool.com/")

        print("\n" + "=" * 50)
        print("ACTION REQUIRED:")
        print("1. Log in to Metricool in the pop-up browser.")
        print("2. Wait until you see your main dashboard.")
        print("3. Come back here and press Enter.")
        print("=" * 50 + "\n")

        input("Press Enter to save cookies...")

        cookies = context.cookies()
        key_path = "keys/metricool_cookies.json"
        os.makedirs(os.path.dirname(key_path), exist_ok=True)

        with open(key_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2)

        print(f"Success! Saved {len(cookies)} cookies to {key_path}")
        print("You can now close the browser.")
        browser.close()


if __name__ == "__main__":
    save_cookies()
