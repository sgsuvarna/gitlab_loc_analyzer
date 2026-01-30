import smtplib
from email.mime.text import MIMEText

def send_error_email(errors, cfg):
    body = ""
    for project, errs in errors.items():
        body += f"\nProject: {project}\n"
        for e in errs:
            body += f"{e['timestamp']} | {e['message']} | {e['context']}\n"

    msg = MIMEText(body)
    msg["Subject"] = "GitLab LOC Analyzer - Soft Errors"
    msg["From"] = cfg["FROM"]
    msg["To"] = ",".join(cfg["TO"])

    with smtplib.SMTP(cfg["SMTP_SERVER"], cfg["PORT"]) as s:
        if cfg.get("USERNAME") and cfg.get("PASSWORD"):
            s.starttls()
            s.login(cfg["USERNAME"], cfg["PASSWORD"])
        s.send_message(msg)
