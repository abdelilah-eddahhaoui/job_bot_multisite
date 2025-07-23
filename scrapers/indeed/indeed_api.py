# ---------------- scrapers/indeed_api.py ----------------
"""
Indeed API scraper – uses JobSpy’s GraphQL client instead of Playwright
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from jobspy import scrape_jobs

from scrapers.base import BaseScraper            # unchanged base.py


class IndeedAPIScraper(BaseScraper):
    """Pull jobs from Indeed via its mobile GraphQL API (JobSpy)"""

    platform = "IndeedAPI"

    # NOTE: keep **kwargs so dashboard can still pass headless=True|False
    def __init__(self, *, output_dir: str | Path = "results", **_):
        super().__init__(headless=True, output_dir=output_dir)

    # ------------------------------------------------------------------ #
    # Public API (same signature the dashboard expects)
    # ------------------------------------------------------------------ #
    def scrape(
        self,
        *,
        keyword: str,
        location: str,
        limit: int = 10,
        hours_old: Optional[int] = None,
    ) -> pd.DataFrame:  # type: ignore[override]
        # --- call JobSpy ------------------------------------------------
        df = scrape_jobs(
            site_name="indeed",
            search_term=keyword,
            location=location,
            results_wanted=limit,
            hours_old=hours_old,
            description_format="markdown",
            country_indeed=location.lower()
        )

        # --- normalise column names your pipeline expects ---------------
        rename_map = {
            "description_markdown": "description",
            "company": "company",
            "job_url": "job_url",
            # jobspy already provides 'title' and 'location'
        }
        df = df.rename(columns=rename_map)

        # guarantee optional columns exist
        for col in ("emails", "easy_apply"):
            if col not in df.columns:
                df[col] = None

        # save CSV via BaseScraper helper
        self._persist_dataframe(df, name=f"indeedAPI_{keyword}_{location}")
        return df

