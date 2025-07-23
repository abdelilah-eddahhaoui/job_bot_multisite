"""Shared Playwright helpers: stealth Chromium context & random sleeps."""
from pathlib import Path
from typing import Tuple
import random, time, logging
from playwright.sync_api import sync_playwright

log = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

_STEALTH_JS = "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"


def rsleep(rng: Tuple[float, float]) -> None:
    time.sleep(random.uniform(*rng))


def create_context(storage_state: Path | None, headless: bool):
    """Return (pw, browser, ctx) with stealth; cookies only if file exists."""
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=headless,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
        ],
    )
    ctx_kwargs = dict(
        viewport={"width": 1280, "height": 1024},
        user_agent=random.choice(USER_AGENTS),
        locale="en-US",
    )
    if storage_state and storage_state.exists():
        ctx_kwargs["storage_state"] = str(storage_state)

    ctx = browser.new_context(**ctx_kwargs)
    ctx.add_init_script(_STEALTH_JS)
    return pw, browser, ctx

