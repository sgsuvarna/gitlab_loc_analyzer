import json, os
from datetime import datetime

FILE = "checkpoint.json"

def load_checkpoint():
    if os.path.exists(FILE):
        try:
            with open(FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None

def save_checkpoint(pid):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump({"last_completed_project_id": pid, "timestamp": datetime.utcnow().isoformat()}, f)

def clear_checkpoint():
    if os.path.exists(FILE):
        os.remove(FILE)
