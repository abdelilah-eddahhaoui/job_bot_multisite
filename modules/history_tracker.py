# modules/history_tracker.py
import json
from pathlib import Path
from datetime import datetime

LOG_PATH = Path("applied_jobs.json")

def _ensure_log():
    LOG_PATH.parent.mkdir(exist_ok=True, parents=True)
    if not LOG_PATH.exists():
        LOG_PATH.write_text("[]", encoding="utf-8")

def has_already_applied(url: str) -> bool:
    _ensure_log()
    data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    return any(item["url"] == url for item in data)

def log_application(
    url: str,
    title: str,
    company: str,
    location: str,
    platform: str,
    status: str = "Applied",       
    timestamp: str | None = None
):
    _ensure_log()
    data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not any(item["url"] == url for item in data):
        data.append({
            "timestamp": timestamp,
            "title": title,
            "company": company,
            "location": location,
            "platform": platform,
            "url": url,
            "status": status,
        })
        LOG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        
def _load_data():
    _ensure_log()
    try:
        return json.loads(LOG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        LOG_PATH.write_text("[]", encoding="utf-8")
        return []        
        
def update_application_status(url: str, new_status: str):
    """
    Find the entry with this URL, update its 'status' field, write file.
    """
    data = _load_data()
    changed = False
    for entry in data:
        if isinstance(entry, dict) and entry.get("url") == url:
            entry["status"] = new_status
            changed = True
    if changed:
        LOG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")