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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("gitlab_loc_analysis.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 60)
    logger.info("Starting GitLab LOC Analysis")
    logger.info("=" * 60)
    
    api = GitLabAPIClient(CONFIG["GITLAB"])
    errors = ErrorCollector()
    
    logger.info("Discovering projects...")
    projects = discover_projects(api, CONFIG)
    projects.sort(key=lambda p: p["id"])
    logger.info(f"Discovered {len(projects)} projects to process")
    
    if not projects:
        logger.warning("No projects found. Check your SCOPE configuration.")
        return

    checkpoint = load_checkpoint()
    resume_after = checkpoint["last_completed_project_id"] if checkpoint else None
    skipping = resume_after is not None
    
    if checkpoint:
        logger.info(f"Resuming from checkpoint. Last completed project ID: {resume_after}")
    else:
        logger.info("No checkpoint found. Starting fresh.")

    all_rows = []
    project_ids = [p["id"] for p in projects]
    
    if resume_after is not None and resume_after not in project_ids:
        logger.warning(f"Resume project ID {resume_after} not found in current project list. Starting from beginning.")
        skipping = False

    total_projects = len(projects)
    processed_count = 0
    skipped_count = 0
    
    for idx, project in enumerate(projects, 1):
        project_name = project.get("path_with_namespace", f"project_{project.get('id')}")
        
        if skipping:
            if project["id"] == resume_after:
                logger.info(f"Found checkpoint project {project_name} (ID: {project['id']}). Resuming from next project.")
                skipping = False
                skipped_count += 1
                continue  # Skip the checkpoint project itself - already processed
            else:
                skipped_count += 1
                logger.debug(f"Skipping project {idx}/{total_projects}: {project_name} (already processed)")
                continue

        logger.info(f"[{idx}/{total_projects}] Processing project: {project_name} (ID: {project['id']})")
        
        rows = calculate_metrics(api, project, CONFIG, errors)
        all_rows.extend(rows)
        
        processed_count += 1
        logger.info(f"Completed project {project_name}: {len(rows)} commits recorded")
        
        save_checkpoint(project["id"])
        logger.debug(f"Checkpoint saved for project ID {project['id']}")

    logger.info("=" * 60)
    logger.info(f"Processing Summary:")
    logger.info(f"Total projects: {total_projects}")
    logger.info(f"Processed: {processed_count}")
    logger.info(f"Skipped (already done): {skipped_count}")
    logger.info(f"Total commits recorded: {len(all_rows)}")
    logger.info("=" * 60)

    logger.info(f"Generating CSV output: {CONFIG['OUTPUT']['CSV_FILE']}")
    generate_csv(all_rows, CONFIG["OUTPUT"]["CSV_FILE"])
    logger.info(f"CSV file generated successfully with {len(all_rows)} rows")

    if CONFIG["DATABASE"]["ENABLED"]:
        logger.info("Inserting data into database...")
        try:
            insert_into_db(all_rows, CONFIG["DATABASE"])
            logger.info(f"Database insert completed: {len(all_rows)} rows")
        except Exception as e:
            logger.error(f"Database insert failed: {str(e)}")
            logger.error("Continuing with error reporting. CSV file was created successfully.")
            # Don't raise - let the job complete and send error notifications

    if CONFIG["EMAIL"]["ENABLED"] and errors.has_errors():
        logger.info("Sending error notification email...")
        send_error_email(errors.errors, CONFIG["EMAIL"])
        logger.info(f"Error email sent with {len(errors.errors)} error(s)")
    elif errors.has_errors():
        logger.warning(f"{len(errors.errors)} error(s) occurred but email notifications are disabled")
    else:
        logger.info("No errors to report")

    clear_checkpoint()
    logger.info("Checkpoint cleared - processing completed successfully")
    
    logger.info("=" * 60)
    logger.info("GitLab LOC Analysis completed")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
