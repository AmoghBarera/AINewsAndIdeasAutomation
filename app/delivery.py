import logging
import smtplib
import requests
from email.message import EmailMessage
from typing import Dict
from app.config import Config

logger = logging.getLogger(__name__)

def chunk_text(text: str, max_length: int = 4000) -> list[str]:
    """Split text into chunks smaller than max_length, preferring to split at headers or double newlines."""
    if len(text) <= max_length:
        return [text]
        
    chunks = []
    current_chunk = ""
    
    # Split by double newline first to keep paragraphs together
    paragraphs = text.split("\n\n")
    
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
        else:
            current_chunk += para + "\n\n"
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

def send_telegram_message(text: str, config: Config) -> bool:
    """Send text via Telegram Bot API."""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials missing, skipping Telegram delivery.")
        return False
        
    if config.DRY_RUN:
        logger.info(f"[DRY RUN] Would send {len(text)} chars to Telegram chat {config.TELEGRAM_CHAT_ID}")
        return True
        
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    
    chunks = chunk_text(text, max_length=4000)
    success = True
    
    for i, chunk in enumerate(chunks):
        payload = {
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            response.raise_for_status()
            logger.info(f"Telegram chunk {i+1}/{len(chunks)} sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send Telegram chunk {i+1}/{len(chunks)}: {e}")
            success = False
            
    return success

def send_email_message(text: str, config: Config) -> bool:
    """Send text via SMTP email."""
    if not config.EMAIL_ENABLED:
        return False
        
    if not all([config.SMTP_HOST, config.SMTP_USERNAME, config.SMTP_PASSWORD, config.EMAIL_TO, config.EMAIL_FROM]):
        logger.warning("Email is enabled but SMTP settings are incomplete. Skipping Email delivery.")
        return False
        
    if config.DRY_RUN:
        logger.info(f"[DRY RUN] Would send email to {config.EMAIL_TO} via {config.SMTP_HOST}")
        return True
        
    msg = EmailMessage()
    msg.set_content(text)
    
    # Extract date from text if possible, else use generic subject
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

def deliver_report(report_text: str, config: Config) -> Dict[str, bool]:
    """Deliver the report via all configured and enabled channels."""
    status = {
        "telegram": False,
        "email": False
    }
    
    logger.info("Starting report delivery phase...")
    
    # Try Telegram
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        status["telegram"] = send_telegram_message(report_text, config)
    else:
        logger.info("Telegram not configured.")
        
    # Try Email
    if config.EMAIL_ENABLED:
        status["email"] = send_email_message(report_text, config)
    else:
        logger.info("Email delivery not enabled.")
        
    return status
