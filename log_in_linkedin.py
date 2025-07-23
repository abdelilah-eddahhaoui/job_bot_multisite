# run:  python login_once.py
from pathlib import Path
from playwright.sync_api import sync_playwright

STATE_FILE = Path("linkedin_state.json")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 …",        # optional
    )
    page = ctx.new_page()
    page.goto("https://www.linkedin.com/login")

    print(
        "\n📌 1) Log in the window that just opened.\n"
        "📌 2) Solve ALL CAPTCHA / security prompts until your home feed loads.\n"
        "📌 3) Close the browser OR press <Enter> here to continue."
    )
    input("👉 When you can see your LinkedIn feed, press <Enter>… ")

    ctx.storage_state(path=STATE_FILE)
    print(f"✅  Session saved to {STATE_FILE.resolve()}")
    browser.close()

