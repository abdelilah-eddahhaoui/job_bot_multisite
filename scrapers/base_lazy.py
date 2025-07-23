"""Mixin: single Chromium, thread wrapper, human delays, smooth scroll."""
from __future__ import annotations
import concurrent.futures, logging
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime, timedelta, timezone

import pandas as pd
from playwright.sync_api import Page

from modules.common.browser_pool import create_context, rsleep

log = logging.getLogger(__name__)


class LazyMixin:
    delay_range: Tuple[float, float] = (3.5, 7.0)

    def __init__(self, *, headless: bool = True, storage_path: str | None = None):
        self.headless = headless
        # convert to Path **only if** not None
        self.storage_path = Path(storage_path) if storage_path else None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._pw = self._browser = self._context = self._page = None  # lazy

    # ---------- public wrapper ----------
    def scrape(self, **kw):
        """Runs the subclass' _scrape_internal inside the worker thread."""
        return self._executor.submit(self._scrape_internal, **kw).result()

    def close(self):
        def _shut():
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()

        self._executor.submit(_shut).result()
        self._executor.shutdown(wait=True)

    # ---------- helpers for subclasses ----------
    def _get_page(self):
        if self._page:
            return self._page
        self._pw, self._browser, self._context = create_context(
            self.storage_path, self.headless
        )
        self._page = self._context.new_page()
        return self._page

    def _pause(self):
        rsleep(self.delay_range)

    @staticmethod
    def _smooth_scroll(page: Page, sel: str, steps: int = 10):
        """Scroll an element to bottom in small steps to trigger lazy load."""
        page.evaluate(
            """(s, n) => {
                const el = document.querySelector(s); if (!el) return;
                const dh = el.scrollHeight / n;
                let y = 0;
                function step() {
                    y += dh;
                    el.scrollTo({top:y, behavior:'smooth'});
                    if (y < el.scrollHeight) setTimeout(step, 300+Math.random()*250);
                }
                step();
            }""",
            sel,
            steps,
        )
        page.wait_for_timeout(3000)

    @staticmethod
    def age_filter(df: pd.DataFrame, hours_old: Optional[int]) -> pd.DataFrame:
        if hours_old is None or "listed_at" not in df.columns:
            return df
        df["listed_at_dt"] = pd.to_datetime(df["listed_at"], errors="coerce", utc=True)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_old)
        keep = df["listed_at_dt"].isna() | (df["listed_at_dt"] >= cutoff)
        return df[keep].drop(columns=["listed_at_dt"])

