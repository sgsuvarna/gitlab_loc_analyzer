import logging
import requests

logger = logging.getLogger(__name__)

def discover_projects(api, cfg):
    projects_by_id = {}
    
    # Discover by project IDs
    for pid in cfg["SCOPE"]["PROJECT_IDS"]:
        try:
            logger.info(f"Fetching project with ID: {pid}")
            project = api.request("GET", f"/projects/{pid}")
            if project and "id" in project:
                projects_by_id[project["id"]] = project
                logger.info(f"Added project: {project.get('path_with_namespace', f'ID {pid}')}")
            else:
                logger.warning(f"Project ID {pid} returned invalid data")
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code
            if status_code == 404:
                logger.warning(f"Project ID {pid} not found (404). Skipping.")
            elif status_code == 403:
                logger.warning(f"Access denied to project ID {pid} (403). Skipping.")
            else:
                logger.error(f"HTTP error {status_code} fetching project ID {pid}: {str(http_err)}")
        except Exception as e:
            logger.error(f"Error fetching project ID {pid}: {str(e)}")
    
    # Discover by group IDs
    for gid in cfg["SCOPE"]["GROUP_IDS"]:
        try:
            logger.info(f"Fetching projects from group ID: {gid}")
            projects = api.paginate(f"/groups/{gid}/projects")
            added_count = 0
            for project in projects:
                if project and "id" in project:
                    projects_by_id[project["id"]] = project
                    added_count += 1
            logger.info(f"Added {added_count} projects from group ID {gid}")
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code
            if status_code == 404:
                logger.warning(f"Group ID {gid} not found (404). Skipping.")
            elif status_code == 403:
                logger.warning(f"Access denied to group ID {gid} (403). Skipping.")
            else:
                logger.error(f"HTTP error {status_code} fetching group ID {gid}: {str(http_err)}")
        except Exception as e:
            logger.error(f"Error fetching projects from group ID {gid}: {str(e)}")
    
    logger.info(f"Project discovery completed. Found {len(projects_by_id)} unique projects.")
    return list(projects_by_id.values())
