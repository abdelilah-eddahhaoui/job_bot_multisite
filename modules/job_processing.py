# ---------------- modules/job_processing.py ----------------
"""
Scrapes a platform, scores each job with the LLM, and (optionally)
generates tailored CV / cover-letters.
"""

from __future__ import annotations

import os
from typing import List, Dict

import pandas as pd
from scrapers.registry import REGISTRY        
from modules.utils import (
    sanitize_filename,
    score_job_match,
    extract_keywords,
)
from modules.cv_generator import insert_keywords_into_doc, convert_to_pdf_libreoffice
from modules.cl_generator import generate_cover_letter, save_to_pdf
from config.profile_loader import load_profile
from modules.history_tracker import has_already_applied

PROFILE = load_profile()
BASE_CV_PATH_EN = "assets/templates/template_cv.docx"
RESULTS_FOLDER = "results"

# keep one scraper instance per platform
_SCRAPER_CACHE: dict[str, object] = {}


# --------------------------------------------------------------------------- #
def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Guarantee columns later code expects."""
    for col in ("description", "emails", "easy_apply"):
        if col not in df.columns:
            df[col] = None
    return df


# --------------------------------------------------------------------------- #
def search_and_process_jobs(
    platform: str,
    search_term: str,
    location: str,
    hours_old: int,
    results_wanted: int = 10,
    score_threshold: int = 7,
    generate_cv: bool = True,
    generate_cl: bool = True,
    headless: bool = False,         ## -----------------> HEADLESS OPTION INSTATIATED HERE (FALSE for now)
    debug: bool = False,
    ea_application: bool = False,
) -> List[Dict]:
    """
    1. Scrape the specified platform via its Playwright scraper.
    2. Score each description with `score_job_match`.
    3. For matches, generate customised CV / cover letters (if selceted in Dashboard) and return a summary.
    """
    os.makedirs(RESULTS_FOLDER, exist_ok=True)

    ScraperCls = REGISTRY.get(platform.lower())
    if ScraperCls is None:
        raise ValueError(f"No scraper registered for platform '{platform}'")

    scraper = _SCRAPER_CACHE.get(platform.lower())
    if scraper is None:
        scraper = ScraperCls(headless=headless)
        _SCRAPER_CACHE[platform.lower()] = scraper
        
    scrape_kwargs = {
        "keyword": search_term,
        "location": location,
        "limit": results_wanted,
        "hours_old": hours_old,
    }
    
    if platform == "linkedin":
        scrape_kwargs["ea_application"] = ea_application

    # -------------- SCRAPE -----------------
    try:
        jobs_df = scraper.scrape(**scrape_kwargs)
    except Exception as exc:
        print(f"{platform} scrape failed: {exc}")
        return []

    if jobs_df.empty:
        print(f"⚠️ No jobs for '{search_term}' in '{location}'")
        return []

    jobs_df = _ensure_columns(jobs_df)

    matched: List[Dict] = []

    # ---------------- MATCH / GENERATE ------------------
    for row in jobs_df.itertuples(index=False):
        desc: str = getattr(row, "description") or ""
        score, reasoning, llm_prompt = score_job_match(desc, debug=debug)
        if score < score_threshold:
            continue


        cv_template = BASE_CV_PATH_EN
        keywords = extract_keywords(desc, debug=debug)
        folder = os.path.join(
            RESULTS_FOLDER, sanitize_filename(f"{row.title}_{row.company}")
        )
        os.makedirs(folder, exist_ok=True)
		
        easy_apply = ea_application
	
        # ---------- dump description ----------------
        desc_file = os.path.join(folder, "description.txt")
        with open(desc_file, "w", encoding="utf-8") as fp:
            fp.write(desc)
        # -------------------------------------------------
        
        # -------- CV -------
        if generate_cv:
            cv_docx = os.path.join(folder, "CV_Custom.docx")
            insert_keywords_into_doc(cv_template, keywords, cv_docx)
            convert_to_pdf_libreoffice(cv_docx, folder)

        # -------- CL -------
        if generate_cl:
            cl_text = generate_cover_letter(
                row.title,
                row.company,
                row.location,
            )
            save_to_pdf(row._asdict(), cl_text, folder)

        if has_already_applied(row.job_url):
            print(f"Skipping {row.job_url} — already applied")
            continue
        
        matched.append(
            {
                "title": row.title,
                "company": row.company,
                "location": row.location,
                "folder": folder,
                "score": score,
                "platform": ScraperCls.platform,
                "email": (
                    row.emails[0]
                    if isinstance(row.emails, list) and row.emails
                    else None
                ),
                "easy_apply": easy_apply,
                "llm_reasoning": reasoning,
                "llm_prompt": llm_prompt,
                "show_reasoning": debug,
                "url": row.job_url,
            }
        )

    return matched

