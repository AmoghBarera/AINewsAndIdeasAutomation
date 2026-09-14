import logging
import smtplib
import os
from email.message import EmailMessage
import markdown
from typing import Dict
from datetime import datetime, timezone
from app.config import Config

logger = logging.getLogger(__name__)

def send_email_message(report_text: str, report_path: str, config: Config) -> bool:
    """Send report via SMTP email (Gmail)."""
    if not config.EMAIL_ENABLED:
        logger.info("Email delivery is disabled.")
        return False
        
    if not all([config.SMTP_HOST, config.SMTP_USERNAME, config.SMTP_PASSWORD, config.EMAIL_TO, config.EMAIL_FROM]):
        logger.warning("Email is enabled but SMTP settings are incomplete. Skipping delivery.")
        return False
        
    if config.DRY_RUN:
        logger.info(f"[DRY RUN] Would send email to {config.EMAIL_TO} via {config.SMTP_HOST}")
        return True
        
    # Extract date for subject
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject = f"{config.EMAIL_SUBJECT_PREFIX} - {today_str}"
    first_line = report_text.split("\n")[0]
    if "Brief — " in first_line:
        subject = first_line.replace("# ", "")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = config.EMAIL_TO
    
    # Generate HTML from markdown
    try:
        html_body = markdown.markdown(report_text)
        msg.set_content(report_text) # Plain text fallback
        msg.add_alternative(html_body, subtype='html')
    except Exception as e:
        logger.warning(f"Could not convert markdown to HTML for email, using plain text: {e}")
        msg.set_content(report_text)
    
    # Attach the markdown file
    if os.path.exists(report_path):
        with open(report_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(report_path)
            msg.add_attachment(file_data, maintype='text', subtype='markdown', filename=file_name)
    
    # Attach the PDF file if it exists
    pdf_path = report_path.replace('.md', '.pdf')
    if os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            file_data = f.read()
            file_name = os.path.basename(pdf_path)
            msg.add_attachment(file_data, maintype='application', subtype='pdf', filename=file_name)

    # Send the email with 1 retry
    import time
    for attempt in range(2):
        try:
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=15) as server:
                server.starttls()
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
                server.send_message(msg)
            logger.info("Email sent successfully.")
            return True
        except Exception as e:
            if attempt == 0:
                logger.warning(f"Failed to send email (attempt 1): {e}. Retrying in 5 seconds...")
                time.sleep(5)
            else:
                logger.error(f"Failed to send email after retries: {e}")
                return False
    return False

def deliver_report(report_path: str, config: Config) -> Dict[str, bool]:
    """Deliver the report via configured channels."""
    status = {
        "email": False
    }
    
    logger.info("Starting report delivery phase...")
    
    if not os.path.exists(report_path):
        logger.error(f"Report file {report_path} not found.")
        return status
        
    with open(report_path, "r", encoding="utf-8") as f:
        report_text = f.read()
        
    # Email Delivery
    status["email"] = send_email_message(report_text, report_path, config)
        
    return status
