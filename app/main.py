# ------------------ app/main.py ------------------
"""
Main entrypoint of the application. Initializes Streamlit UI and invokes job processing logic.
"""

import os, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent   # job_bot_multisite/
os.chdir(ROOT)                                         # make it the CWD
sys.path.insert(0, str(ROOT))                          # let “from app …” work

from app.dashboard import run_dashboard


if __name__ == "__main__":
    run_dashboard()
