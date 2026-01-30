def discover_projects(api, cfg):
    projects_by_id = {}
    for pid in cfg["SCOPE"]["PROJECT_IDS"]:
        project = api.request("GET", f"/projects/{pid}")
        if project and "id" in project:
            projects_by_id[project["id"]] = project
    for gid in cfg["SCOPE"]["GROUP_IDS"]:
        for project in api.paginate(f"/groups/{gid}/projects"):
            if project and "id" in project:
                projects_by_id[project["id"]] = project
    return list(projects_by_id.values())
