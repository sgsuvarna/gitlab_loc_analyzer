from config import GITLAB, SCOPE, COMPARISON, FILTERS, DATABASE, EMAIL, OUTPUT
from api_client import GitLabAPIClient
from project_discovery import discover_projects
from metrics_calculation import calculate_metrics
from error_collector import ErrorCollector
from output_generation import generate_csv, insert_into_db
from email_notifier import send_error_email
from checkpoint import load_checkpoint, save_checkpoint, clear_checkpoint
import logging

CONFIG = {
    "GITLAB": GITLAB,
    "SCOPE": SCOPE,
    "COMPARISON": COMPARISON,
    "FILTERS": FILTERS,
    "DATABASE": DATABASE,
    "EMAIL": EMAIL,
    "OUTPUT": OUTPUT,
}

logging.basicConfig(filename="error_log.txt", level=logging.ERROR)

def main():
    api = GitLabAPIClient(CONFIG["GITLAB"])
    errors = ErrorCollector()
    projects = discover_projects(api, CONFIG)
    projects.sort(key=lambda p: p["id"])

    checkpoint = load_checkpoint()
    resume_after = checkpoint["last_completed_project_id"] if checkpoint else None
    skipping = resume_after is not None

    all_rows = []
    project_ids = [p["id"] for p in projects]
    
    if resume_after is not None and resume_after not in project_ids:
        logging.warning(f"Resume project ID {resume_after} not found in current project list. Starting from beginning.")
        skipping = False

    for project in projects:
        if skipping:
            if project["id"] == resume_after:
                skipping = False
            continue

        rows = calculate_metrics(api, project, CONFIG, errors)
        all_rows.extend(rows)
        save_checkpoint(project["id"])

    generate_csv(all_rows, CONFIG["OUTPUT"]["CSV_FILE"])

    if CONFIG["DATABASE"]["ENABLED"]:
        insert_into_db(all_rows, CONFIG["DATABASE"])

    if CONFIG["EMAIL"]["ENABLED"] and errors.has_errors():
        send_error_email(errors.errors, CONFIG["EMAIL"])

    clear_checkpoint()

if __name__ == "__main__":
    main()
