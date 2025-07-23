# ------------------ app/main.py ------------------
"""
Main entrypoint of the application. Initializes Streamlit UI and invokes job processing logic.
"""
from app.dashboard import run_dashboard

if __name__ == "__main__":
    run_dashboard()