import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    # Telegram config (Legacy)
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None
    
    EMAIL_ENABLED: bool = False
    EMAIL_PROVIDER: str = "gmail"
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAIL_TO: str | None = None
    EMAIL_FROM: str | None = None
    EMAIL_SUBJECT_PREFIX: str = "Daily Tech & AI Brief"

    TIMEZONE_OFFSET_HOURS: int = 0
    MAX_NEWS_ITEMS: int = 30
    SUMMARY_WORDS_MIN: int = 900
    SUMMARY_WORDS_MAX: int = 1100
    IDEA_COUNT: int = 10
    ENABLE_IDEA_CRITIC: bool = True
    DRY_RUN: bool = False
    OUTPUT_DIR: str = "output"
    DATA_DIR: str = "data"
    GENERATE_PDF: bool = False

def load_config() -> Config:
    load_dotenv(override=True)
    
    config = Config(
        GEMINI_API_KEY=os.getenv("GEMINI_API_KEY"),
        GROQ_API_KEY=os.getenv("GROQ_API_KEY"),
        # Legacy Telegram
        TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN"),
        TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID"),
        # Email settings
        EMAIL_ENABLED=os.getenv("EMAIL_ENABLED", "false").lower() == "true",
        EMAIL_PROVIDER=os.getenv("EMAIL_PROVIDER", "gmail"),
        SMTP_HOST=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        SMTP_PORT=int(os.getenv("SMTP_PORT", "587")),
        SMTP_USERNAME=os.getenv("SMTP_USERNAME"),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD"),
        EMAIL_TO=os.getenv("EMAIL_TO"),
        EMAIL_FROM=os.getenv("EMAIL_FROM"),
        EMAIL_SUBJECT_PREFIX=os.getenv("EMAIL_SUBJECT_PREFIX", "Daily Tech & AI Brief"),
        # Pipeline settings
        TIMEZONE_OFFSET_HOURS=int(os.getenv("TIMEZONE_OFFSET_HOURS", "0")),
        MAX_NEWS_ITEMS=int(os.getenv("MAX_NEWS_ITEMS", "30")),
        SUMMARY_WORDS_MIN=int(os.getenv("SUMMARY_WORDS_MIN", 900)),
        SUMMARY_WORDS_MAX=int(os.getenv("SUMMARY_WORDS_MAX", 1100)),
        IDEA_COUNT=int(os.getenv("IDEA_COUNT", 10)),
        ENABLE_IDEA_CRITIC=os.getenv("ENABLE_IDEA_CRITIC", "true").lower() == "true",
        DRY_RUN=os.getenv("DRY_RUN", "false").lower() == "true",
        OUTPUT_DIR=os.getenv("OUTPUT_DIR", "output"),
        DATA_DIR=os.getenv("DATA_DIR", "data"),
        GENERATE_PDF=os.getenv("GENERATE_PDF", "false").lower() == "true"
    )
    return config
