import logging

logger = logging.getLogger(__name__)

def calculate_metrics(api, project, cfg, errors):
    rows = []
    project_name = project.get("path_with_namespace", f"project_{project.get('id', 'unknown')}")
    
    logger.info(f"Starting metrics calculation for project: {project_name} (ID: {project.get('id', 'unknown')})")
    
    try:
        commits = api.request(
            "GET",
            f"/projects/{project['id']}/repository/compare",
            {"from": cfg["COMPARISON"]["FROM_REF"], "to": cfg["COMPARISON"]["TO_REF"]}
        ).get("commits", [])
    except Exception as e:
        logger.error(f"Failed to fetch commits for project {project_name}: {str(e)}")
        errors.add(project_name, f"Failed to fetch commits: {str(e)}", {"project_id": project.get("id")})
        return rows

    total_commits = len(commits)
    logger.info(f"Found {total_commits} commits between {cfg['COMPARISON']['FROM_REF']} and {cfg['COMPARISON']['TO_REF']} for project {project_name}")
    
    processed_commits = 0
    skipped_merge_commits = 0
    skipped_files_total = 0
    
    filter_enabled = cfg.get("FILTERS", {}).get("USE_DIFF_FILE_FILTERING", False)
    excluded_extensions = cfg.get("FILTERS", {}).get("EXCLUDED_FILE_EXTENSIONS", [])
    
    if filter_enabled:
        logger.info(f"File filtering enabled. Excluded extensions: {excluded_extensions}")
    else:
        logger.info("File filtering is disabled")

    for c in commits:
        commit_id = c.get("id", "unknown")
        try:
            if cfg.get("FILTERS", {}).get("EXCLUDE_MERGE_COMMITS", True) and len(c.get("parent_ids", [])) > 1:
                logger.debug(f"Skipping merge commit {commit_id[:8]} in project {project_name}")
                skipped_merge_commits += 1
                continue

            logger.debug(f"Processing commit {commit_id[:8]}: {c.get('title', 'No title')[:50]}...")

            try:
                diffs = api.request("GET", f"/projects/{project['id']}/repository/commits/{c['id']}/diff")
                add = delete = 0
                files_processed = 0
                files_skipped = 0
                
                for d in diffs:
                    file_path = d.get("new_path", "") or d.get("old_path", "")
                    
                    if filter_enabled and excluded_extensions and file_path:
                        should_skip = any(file_path.lower().endswith(ext.lower()) for ext in excluded_extensions)
                        if should_skip:
                            logger.debug(f"Skipping file {file_path} due to excluded extension")
                            files_skipped += 1
                            skipped_files_total += 1
                            continue
                    
                    files_processed += 1
                    file_add = file_delete = 0
                    for line in d.get("diff", "").splitlines():
                        if line.startswith("+") and not line.startswith("+++"):
                            file_add += 1
                        elif line.startswith("-") and not line.startswith("---"):
                            file_delete += 1
                    
                    add += file_add
                    delete += file_delete
                
                if files_skipped > 0:
                    logger.info(f"Commit {commit_id[:8]}: Processed {files_processed} files, skipped {files_skipped} filtered files")
            except Exception as diff_error:
                logger.warning(f"Diff calculation failed for commit {commit_id[:8]} in project {project_name}, falling back to stats API: {str(diff_error)}")
                try:
                    stats_response = api.request("GET", f"/projects/{project['id']}/repository/commits/{c['id']}", {"stats": True})
                    stats = stats_response.get("stats", {})
                    add, delete = stats.get("additions", 0), stats.get("deletions", 0)
                    logger.info(f"Using stats API for commit {commit_id[:8]}: +{add}/-{delete}")
                except Exception as stats_error:
                    logger.error(f"Stats API also failed for commit {commit_id[:8]}: {str(stats_error)}")
                    errors.add(project_name, f"Failed to get metrics for commit {commit_id[:8]}: {str(stats_error)}", {"commit": commit_id})
                    continue

            if add > 0 or delete > 0:
                logger.debug(f"Commit {commit_id[:8]} metrics: +{add}/-{delete}")
            
            rows.append({
                "project": project_name,
                "FromBranch": cfg["COMPARISON"]["FROM_REF"],
                "ToBranch": cfg["COMPARISON"]["TO_REF"],
                "CommitSHA": c["id"],
                "Title": c.get("title", "No title"),
                "AuthorName": c.get("author_name", "Unknown"),
                "AuthorEmail": c.get("author_email", ""),
                "Date": c.get("created_at", ""),
                "LinesAdded": add,
                "LinesDeleted": delete,
                "TotalChanges": add + delete
            })
            
            processed_commits += 1

        except Exception as e:
            logger.error(f"Error processing commit {commit_id[:8]} in project {project_name}: {str(e)}")
            errors.add(project_name, str(e), {"commit": commit_id})

    logger.info(f"Completed project {project_name}: {processed_commits}/{total_commits} commits processed, {skipped_merge_commits} merge commits skipped, {skipped_files_total} files filtered")
    
    return rows
