# ----------------- scrapers/base.py -----------------
"""Abstract helper every site scraper inherits from, serving as a 'skull' for the future scrapers """

from __future__ import annotations
import abc, os
from pathlib import Path
import pandas as pd
from dataclasses import asdict, is_dataclass


class BaseScraper(abc.ABC):
    """Minimal common API – subclasses must implement scrape()."""

    def __init__(self, *, headless: bool = True, output_dir: str | os.PathLike = "results"):
        self.headless   = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @abc.abstractmethod
    def scrape(
        self,
        *,
        keyword: str,
        location: str,
        limit: int = 10,
        hours_old: int | None = None,
    ) -> pd.DataFrame: ...

    # ---------------- convenience helpers ----------------
    @staticmethod
    def _to_dataframe(postings: list) -> pd.DataFrame:
        """Convert list[JobPosting] → pd.DataFrame"""
        if not postings:
            return pd.DataFrame()
        rows = [
            asdict(p) if is_dataclass(p) else vars(p)         # works with __slots__
            for p in postings
        ]
        return pd.DataFrame(rows)

    def _persist_dataframe(self, df: pd.DataFrame, *, name: str) -> Path:
        """Save CSV to results/ and return its Path."""
        csv_path = self.output_dir / f"{name}.csv"
        df.to_csv(csv_path, index=False)
        return csv_path

