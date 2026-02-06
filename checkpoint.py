import json, os
from datetime import datetime
import logging

FILE = "checkpoint.json"
logger = logging.getLogger(__name__)

def load_checkpoint():
    if os.path.exists(FILE):
        try:
            with open(FILE, "r", encoding="utf-8") as f:
                checkpoint = json.load(f)
                logger.info(f"Loaded checkpoint: {checkpoint}")
                return checkpoint
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load checkpoint file: {str(e)}")
            return None
    return None

def save_checkpoint(pid):
    try:
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump({"last_completed_project_id": pid, "timestamp": datetime.utcnow().isoformat()}, f)
        logger.debug(f"Checkpoint saved: project ID {pid}")
    except IOError as e:
        logger.warning(f"Failed to save checkpoint for project ID {pid}: {str(e)}")
        logger.warning("Continuing without checkpoint. Job cannot be resumed if it fails.")
    except Exception as e:
        logger.error(f"Unexpected error saving checkpoint: {str(e)}")

def clear_checkpoint():
    try:
        if os.path.exists(FILE):
            os.remove(FILE)
            logger.info("Checkpoint file cleared")
    except OSError as e:
        logger.warning(f"Failed to clear checkpoint file: {str(e)}")
