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
You are a senior technical writer finishing a pre-formatted cover letter template.

**Task**  
Fill in *only* the text inside placeholders `[[...]]`.  
Do **not** change any other part of the template.

**Candidate**  
{NAME} — {BACKGROUND}

**Real Experience**  
{EXPERIENCE}

**Position to Apply For**  
• Job Title: {{job_title}}  
• Company  : {{company}}  
• Location : {{location}}

**Writing Rules** (strict)  
1. Language: professional, fluent **English**.  
2. Fill *only* the `[[...]]` fields—no extra brackets, no template edits.  
3. Ground every sentence in *actual* experience or the supplied job description.  
4. Never invent numbers, job titles, or achievements.  
5. Prefer action verbs: *coordinate*, *analyse*, *optimise*, *document*, *prototype*…  
6. If the job description is vague, reference high-level themes (e.g. “fluid-system design”, “computational optimisation workflows”) rather than guessing specifics.  
7. No clichés (“perfect fit”, “lifelong dream”, etc.).

**Output**  
Return the completed letter—nothing else, no markdown.

Template to complete  
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