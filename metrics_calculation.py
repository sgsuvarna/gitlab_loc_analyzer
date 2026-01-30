import re

def calculate_metrics(api, project, cfg, errors):
    rows = []
    commits = api.request(
        "GET",
        f"/projects/{project['id']}/repository/compare",
        {"from": cfg["COMPARISON"]["FROM_REF"], "to": cfg["COMPARISON"]["TO_REF"]}
    ).get("commits", [])

    for c in commits:
        commit_id = c.get("id", "unknown")
        try:
            if cfg["FILTERS"]["EXCLUDE_MERGE_COMMITS"] and len(c.get("parent_ids", [])) > 1:
                continue

            try:
                diffs = api.request("GET", f"/projects/{project['id']}/repository/commits/{c['id']}/diff")
                add = delete = 0
                for d in diffs:
                    for line in d.get("diff", "").splitlines():
                        if line.startswith("+") and not line.startswith("+++"):
                            add += 1
                        elif line.startswith("-") and not line.startswith("---"):
                            delete += 1
            except Exception:
                stats = api.request("GET", f"/projects/{project['id']}/repository/commits/{c['id']}", {"stats": True})["stats"]
                add, delete = stats["additions"], stats["deletions"]

            rows.append({
                "project": project["path_with_namespace"],
                "FromBranch": cfg["COMPARISON"]["FROM_REF"],
                "ToBranch": cfg["COMPARISON"]["TO_REF"],
                "CommitSHA": c["id"],
                "Title": c["title"],
                "AuthorName": c["author_name"],
                "AuthorEmail": c["author_email"],
                "Date": c["created_at"],
                "LinesAdded": add,
                "LinesDeleted": delete,
                "TotalChanges": add + delete
            })

        except Exception as e:
            errors.add(project["path_with_namespace"], str(e), {"commit": commit_id})

    return rows
