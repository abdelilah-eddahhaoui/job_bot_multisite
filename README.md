# Job‑Bot‑Multisite (Linkedin, Indeed for now) (Python 3.12)

> **What is Job-Bot-Multisite?**  
> A personal, end-to-end pipeline that turns dozens of job-board tabs and copy-pasting chores into one click.  
> Built in my free evenings (by a mechanical-engineering graduate with no formal CS degree and only a good python experience), it scrapes fresh listings, ranks them with an LLM, auto-tailors my CV & cover letter, and tracks every application in a single Streamlit dashboard.  
> The goal: remove ~80 % of the repetitive work so I can spend time on what actually matters—targeted outreach and continuous learning.


| Feature | What it does |
|---------|--------------|
| **Streamlit dashboard** | Point‑and‑click UI for the whole workflow |
| **Keyword search** | Upload a '.txt' list **or** paste keywords |
| **Job scraping** | Indeed (API) via `jobspy` · LinkedIn (Browser) with Playwright |
| **Relevance scoring** | Local Llama 3 (via **Ollama**) *or* OpenAI GPT‑3.5 |
| **CV tailoring** | Injects keywords into `assets/templates/template_cv.docx`, keeps it 1‑page, outputs **DOCX + PDF** (extremely case sensitive and still Alpha versioned) |
| **Cover‑letter wizard** | Generates personalised cover letter (DOCX + PDF) from a template (Always recheck if no errors or badly generated letters result from the LLM reasoning) |
| **Outreach** | Saves Gmail drafts with attachments (idea, still not developed) |
| **Application history** | Tracks status (Applied / Interview / Offered / Rejected) |
| **Manual entry** | Paste any job description then generate a modified CV + tailored CL |

---

## 1 · Prerequisites

| Dependency | Why | Install |
|------------|-----|---------|
| **Python 3.12** | Required runtime | 'pyenv' / system installer |
| **LibreOffice ≥ 7** | DOCX → PDF conversion | `sudo apt install libreoffice` |
| **Google Chrome / Edge** (optional) | LinkedIn scraping |
| **ChromeDriver / msedgedriver** | Matches browser version | handled by `webdriver‑manager` |
| **Ollama** | Local Llama 3‑8B | <https://ollama.com/download> |

---

## 2 · Setup

```bash
git clone https://github.com/abdelilah-eddahhaoui/job_bot_multisite.git
cd job_bot_multisite

python3.12 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3 · First run

```bash
streamlit run app/main.py
```

1. **Home tab -> Profile** — fill once; saved to 'config/profile.json'
2. **Place your base CV** — 'assets/templates/template_cv.docx'
3. **Place your base CL** — 'assets/templates/template_motivation.docx'
---

## 4 · Workflow

1. **Search** — add / edit keywords, start search  
2. **Results** — tailor CV & CL per listing   
3. **History** — track application status

---

## 5 · LLM back‑ends

| Engine | How |
|--------|-----|
| **Ollama (default)** | Ensure 'ollama run llama3' works |
| **OpenAI API** | Select in UI, paste 'OPENAI_API_KEY' |

---

## 6 · Smoke test

```bash
python - <<'PY'
from modules.cv_generator import insert_keywords_into_doc, convert_to_pdf_libreoffice
import os, shutil, pathlib, tempfile
os.makedirs("tmp", exist_ok=True)
insert_keywords_into_doc("assets/templates/template_cv.docx",
                         ["communication", "first aid", "meal prep"],
                         "tmp/test_cv.docx")
convert_to_pdf_libreoffice("tmp/test_cv.docx", "tmp")
assert pathlib.Path("tmp/test_cv.pdf").exists()
print("CV pipeline OK")
PY
```

---

## Project tree (key folders)

```
app/                    # Streamlit UI
modules/                # CV, CL, scraping, utils
scrapers/               # Site‑specific logic
assets/templates/       # template_cv.docx, template_motivation.docx
results/                # generated docs per job
config/profile.json     # your private profile (git‑ignored)
```

---

## Acknowledgements

This project relies on  
**[JobSpy](https://github.com/adamlui/jobspy)** for its Indeed searching & parsing utilities.  
Huge thanks to the JobSpy authors for open-sourcing their code.

## License

by : Abdelilah Ed dahhaoui (Demo data only ; users must replace templates with their own)
Templates source : https://create.microsoft.com/en-us/template/industry-manager-resume-57cae682-222c-4646-9a80-c404ee5c5d7e