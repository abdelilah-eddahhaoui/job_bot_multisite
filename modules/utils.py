# ------------------ modules/utils.py ------------------
"""
Utility functions for common operations.
Dependencies: ollama, langdetect
"""
import os
import re
import logging

import streamlit as st
from config.profile_loader import load_profile
from modules.prompts import CV_KEYWORD_EXTRACTION_PROMPT, SCORE_JOB_MATCH_PROMPT

RAW_PROFILE = load_profile() or {}
PROFILE = {
    "background": RAW_PROFILE.get("background", ""),
    "skills": RAW_PROFILE.get("skills", []),
    "objective": RAW_PROFILE.get("objective", "")
}
log = logging.getLogger(__name__)


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?"<>|#:;,]', "_", name)


def load_search_terms(file_path: str) -> list[str]:
    """Read newline-separated keywords, ignoring commented lines (# …)."""
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    except Exception as exc:
        log.warning("⚠️ Failed to read keyword file %s → %s", file_path, exc)
        return []


# --------------------------------------------------------------------- #
#  L L M  helpers
# --------------------------------------------------------------------- #

def llm_chat(messages: list[dict], model: str):
    """
    Dispatch either to Ollama or OpenAI v1.x API, returning a dict
    with {"message": {"content": ...}}.
    """
    backend = os.getenv("LLM_BACKEND", "ollama")

    if backend == "openai":
        # New 1.0+ interface
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
        resp = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return {"message": {"content": resp.choices[0].message.content}}

    else:
        # Your existing Ollama logic
        import ollama
        return ollama.chat(model=model, messages=messages)


def extract_keywords(job_desc: str, *, debug: bool = False) -> list[str]:
    """Return up to 15 keywords extracted by the LLM."""
    if not job_desc or len(job_desc.strip()) < 20:
        return []

    prompt = CV_KEYWORD_EXTRACTION_PROMPT.format(job_desc=job_desc)

    try:
        model = "gpt-3.5-turbo" if os.getenv("LLM_BACKEND")=="openai" else "llama3"
        resp = llm_chat([{"role":"user","content":prompt}], model=model)

        # allow comma **or** newline separated output
        content = resp["message"]["content"]
        items = [kw.strip() for kw in re.split(r"[,;\n]+", content)]
        
        failure_phrases = (
            "unfortunately",            
            "does not contain",         
            "no specific", "no relevant",
            "no keyword"               
        )

        keywords = [
            kw for kw in items
            if kw
            and not kw.lower().startswith("here")          
            and not kw.strip().lower().startswith(failure_phrases)
            and len(kw.split()) <= 3                       
            and len(kw) <= 30                             
        ]

        # If nothing survives, signal “no keywords found”
        return keywords[:15] if keywords else []

    except Exception as exc:
        log.warning("⚠️ Keyword extraction failed: %s", exc)
        if debug:
            raise 
        return []

def score_job_match(job_desc: str, *, debug: bool = False) -> tuple[int, str, str]:
    """
    Ask the LLM for a 0-10 suitability score.
    Returns (score, reasoning, prompt)
    """
    prompt = SCORE_JOB_MATCH_PROMPT.format(job_desc=job_desc)

    try:
        model = "gpt-3.5-turbo" if os.getenv("LLM_BACKEND")=="openai" else "llama3"
        resp = llm_chat([{"role":"user","content":prompt}], model=model)
        content = resp["message"]["content"].strip()

        m = re.search(r"\bscore\s*[=:]?\s*(\d+)", content, flags=re.I) or \
            re.search(r"(\d+)", content)
        score = int(m.group(1)) if m else 0
        score = max(0, min(score, 10))        # allow genuine zero

        if debug:
            st.expander("LLM score prompt / response").code(
                f"### PROMPT\n{prompt}\n\n### RESPONSE\n{content}"
            )

        return score, content, prompt

    except Exception as exc:
        log.warning("⚠️ scoring failed: %s", exc)
        if debug:
            st.error(f"LLM scoring error: {exc}")
        return 0, f"[Error: {exc}]", prompt
