import json, os
from datetime import datetime

FILE = "checkpoint.json"

def load_checkpoint():
    if os.path.exists(FILE):
        with open(FILE) as f:
            return json.load(f)
    return None

def save_checkpoint(pid):
    with open(FILE, "w") as f:
        json.dump({"last_completed_project_id": pid, "timestamp": datetime.utcnow().isoformat()}, f)

def clear_checkpoint():
    if os.path.exists(FILE):
        os.remove(FILE)
