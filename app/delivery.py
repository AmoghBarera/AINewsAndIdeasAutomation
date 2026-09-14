import logging
import smtplib
import requests
import time
import os
from email.message import EmailMessage
from typing import Dict
from datetime import datetime, timezone
from app.config import Config

logger = logging.getLogger(__name__)

TELEGRAM_MAX_MESSAGE_LENGTH = 4000

def send_telegram_message(text: str, config: Config) -> bool:
    """Send text via Telegram Bot API with 1 retry."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials missing, skipping Telegram message delivery.")
        return False
        
    if config.DRY_RUN:
        logger.info(f"[DRY RUN] Would send Telegram message: {text[:100]}...")
        return True
        
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    for attempt in range(2):
        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            logger.info("Telegram message sent successfully.")
            return True
        except Exception as e:
            logger.warning(f"Telegram message attempt {attempt+1} failed: {e}")
            if attempt == 0:
                time.sleep(5)
                
    logger.error("Failed to send Telegram message after retries.")
    return False

def send_telegram_document(file_path: str, config: Config) -> bool:
    """Send file via Telegram Bot API with 1 retry."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        return False
        
    if config.DRY_RUN:
        logger.info(f"[DRY RUN] Would send file {file_path} to Telegram")
        return True
        
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendDocument"
    
    for attempt in range(2):
        try:
            with open(file_path, 'rb') as f:
                files = {'document': f}
                data = {'chat_id': config.TELEGRAM_CHAT_ID}
                response = requests.post(url, data=data, files=files, timeout=30)
                response.raise_for_status()
            logger.info(f"Telegram document {os.path.basename(file_path)} sent successfully.")
            return True
        except Exception as e:
            logger.warning(f"Telegram document attempt {attempt+1} failed: {e}")
            if attempt == 0:
                time.sleep(5)
                
    logger.error("Failed to send Telegram document after retries.")
    return False

def send_email_message(text: str, config: Config) -> bool:
    """Send text via SMTP email."""
    if not config.EMAIL_ENABLED:
        return False
        
    if not all([config.SMTP_HOST, config.SMTP_USERNAME, config.SMTP_PASSWORD, config.EMAIL_TO, config.EMAIL_FROM]):
        logger.warning("Email is enabled but SMTP settings are incomplete. Skipping.")
        return False
        
    if config.DRY_RUN:
        logger.info(f"[DRY RUN] Would send email to {config.EMAIL_TO}")
        return True
        
    msg = EmailMessage()
    msg.set_content(text)
    
    subject = "Daily Tech & AI Opportunity Brief"
    first_line = text.split("\n")[0]
    if "Brief — " in first_line:
        subject = first_line.replace("# ", "")
        
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_FROM
    msg["To"] = config.EMAIL_TO
    
    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Email sent successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def deliver_report(report_path: str, config: Config) -> Dict[str, bool]:
    """Deliver the report via all configured channels."""
    status = {
        "telegram": False,
        "email": False
    }
    
    logger.info("Starting report delivery phase...")
    
    if not os.path.exists(report_path):
        logger.error(f"Report file {report_path} not found.")
        return status
        
    with open(report_path, "r", encoding="utf-8") as f:
        report_text = f.read()

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # Try Telegram
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        # First send notification message
        notification = f"Daily Tech & AI Opportunity Brief generated for {today_str}"
        send_telegram_message(notification, config)
        
        # Then send report content
        if len(report_text) <= TELEGRAM_MAX_MESSAGE_LENGTH:
            status["telegram"] = send_telegram_message(report_text, config)
        else:
            status["telegram"] = send_telegram_document(report_path, config)
    else:
        logger.info("Telegram not configured.")
        
    # Try Email
    if config.EMAIL_ENABLED:
        status["email"] = send_email_message(report_text, config)
    else:
        logger.info("Email delivery not enabled.")
        
    return status
