# ── modules/prompts.py  ─────────────────────────────────────────────
"""
Strict and detailed prompts.
All personal data is filled at runtime from `config/profile.json`.
"""

from textwrap import dedent
from config.profile_loader import profile_field

# -------------------------------------------------------------------
# Helper strings built from the JSON profile
NAME        = profile_field("name", "")
BACKGROUND  = profile_field("background", "")
SKILLS      = ", ".join(profile_field("skills", []))
EXPERIENCE  = "• " + "\n• ".join(profile_field("experience_bullets", []))
OBJECTIVE   = profile_field("objective", "")
INDUSTRIES  = ", ".join(profile_field("preferred_industries", []))

# -------------------------------------------------------------------
# COVER-LETTER PROMPT
COVER_LETTER_PROMPT = dedent(f"""
You are filling a cover-letter template whose blanks are runs of
three or more underscores (e.g. `__________`).

────────────── JOB CONTEXT ──────────────
Company  : {{company}}
Job title: {{job_title}}
Location : {{location}}

───────── CANDIDATE PROFILE ─────────
Name       : {NAME}
Background : {BACKGROUND}
Core skills: {SKILLS}
Experience :
{EXPERIENCE}

───────── STRICT RULES ─────────
1. Replace every run of underscores with the correct information.
   • Blank after “Dear Hiring Team at” → Company  
   • Blank after “position of”         → Job title  
   • Lines of underscores under “roles such as:” → one past-experience
     line per role **without any bullet symbol**.  
     (Duplicate the blank line template if you need more lines; remove
      unused lines if you need fewer.)
   • Any other blank → best matching detail, or delete the underscores
     entirely if no data exists.
2. Do **not** add bullets, dashes or other list markers anywhere.
3. Keep punctuation, line breaks, and spacing exactly as given.
4. Return the completed template **plain text only**.

──────── TEMPLATE START ────────
{{template_text}}
""").strip()


# -------------------------------------------------------------------
# KEYWORD-EXTRACTION PROMPT  
CV_KEYWORD_EXTRACTION_PROMPT = dedent("""
You are a technical assistant analysing a job description.

Extract the **10–15 most precise technical keywords** (tools, methods, domains, technologies).  
• Exclude soft skills and duplicates.  
• Keep acronyms and exact casing.  
• Return **one** comma-separated line, sorted by importance.

Job Description:  
{{job_desc}}
""").strip()

# -------------------------------------------------------------------
# JOB-MATCH SCORING PROMPT
SCORE_JOB_MATCH_PROMPT = dedent(f"""
You are a recruiter assistant rating how well a job matches the candidate.

**Candidate Snapshot**  
• Background : {BACKGROUND}  
• Core Skills: {SKILLS}  
• Objective  : {OBJECTIVE}  
• Preferred industries: {INDUSTRIES}

**Job Description**  
{{job_desc}}

**Instructions**  
1. Return exactly **one integer 1-10**.  
2. Add **one concise sentence** justifying the score (no lists, no headings).  
3. Base the score on:  
   – Technical overlap (tools, domains)  
   – Alignment with past experience  
   – Fit with stated objective/industries  
   – Familiar workflows (e.g. CFD, FEA, Python, SU2, ANSYS)  
4. Penalise if the role is in a completely different field, even if some tools match.

**Format Example**  
7 – Uses Python and CFD tools the candidate knows, but the role focuses on IT infrastructure rather than physical simulation.
""").strip()
# ────────────────────────────────────────────────────────────────────