# ----------------- scrapers/models.py -----------------
from dataclasses import dataclass

@dataclass(slots=True, frozen=True)
class JobPosting:
    """Typed representation of one job result."""

    title: str
    company: str
    location: str
    job_id: str
    job_url: str
    listed_at: str | None = None  # ISO‑8601 string if available
    description: str | None = None
    emails: list[str] | None = None
    easy_apply: bool = False