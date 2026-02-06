GITLAB = {
    "BASE_URL": "https://gitlab.com/api/v4",
    "PRIVATE_TOKEN": "DUMMY_TOKEN",
    "REQUEST_TIMEOUT": 30,
    "MAX_RETRIES": 5,
    "BACKOFF_FACTOR": 2
}

SCOPE = {"PROJECT_IDS": [], "GROUP_IDS": []}

COMPARISON = {"FROM_REF": "rel_1", "TO_REF": "rel_2"}

FILTERS = {
    "EXCLUDE_MERGE_COMMITS": True,
    "USE_DIFF_FILE_FILTERING": True,
    "EXCLUDED_FILE_EXTENSIONS": [".csv", ".xlsx", ".txt", ".md", ".json", ".xml", ".yaml", ".yml", ".ini", ".conf", ".config", ".log", ".svg", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".pdf", ".doc", ".docx", ".ppt", ".pptx"]
}

DATABASE = {
    "ENABLED": False,
    "HOST": "",
    "PORT": 1521,
    "SERVICE": "",
    "USER": "",
    "PASSWORD": "",
    "TABLE": "",
    "COLUMNS": []
}

EMAIL = {
    "ENABLED": False,
    "FROM": "",
    "TO": [],
    "SMTP_SERVER": "",
    "PORT": 25,
    "USERNAME": "",
    "PASSWORD": ""
}

OUTPUT = {"CSV_FILE": "gitlab_loc_report.csv"}