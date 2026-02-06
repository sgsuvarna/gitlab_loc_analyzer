import smtplib
from email.mime.text import MIMEText
import logging

logger = logging.getLogger(__name__)

def send_error_email(errors, cfg):
    try:
        body = ""
        for project, errs in errors.items():
            body += f"\nProject: {project}\n"
            for e in errs:
                body += f"{e['timestamp']} | {e['message']} | {e['context']}\n"

        msg = MIMEText(body)
        msg["Subject"] = "GitLab LOC Analyzer - Soft Errors"
        msg["From"] = cfg["FROM"]
        msg["To"] = ",".join(cfg["TO"])

        logger.info(f"Sending error notification email to {cfg['TO']}")
        
        with smtplib.SMTP(cfg["SMTP_SERVER"], cfg["PORT"]) as s:
            if cfg.get("USERNAME") and cfg.get("PASSWORD"):
                logger.debug("Using SMTP authentication")
                s.starttls()
                s.login(cfg["USERNAME"], cfg["PASSWORD"])
            s.send_message(msg)
        
        logger.info("Error notification email sent successfully")
        
    except smtplib.SMTPException as smtp_err:
        logger.error(f"Failed to send error email via SMTP: {str(smtp_err)}")
        logger.error("Email notification failed, but analysis completed successfully")
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        logger.error("Email notification failed, but analysis completed successfully")
