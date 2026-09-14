import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    LLM_PROVIDER: str = "mock"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    EMAIL_ENABLED: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_TO: str = ""
    EMAIL_FROM: str = ""
    TIMEZONE_OFFSET_HOURS: int = 0
    MAX_NEWS_ITEMS: int = 30
    SUMMARY_WORDS_MIN: int = 900
    SUMMARY_WORDS_MAX: int = 1100
    IDEA_COUNT: int = 10
    DRY_RUN: bool = False
    OUTPUT_DIR: str = "output"
    DATA_DIR: str = "data"

def load_config() -> Config:
    load_dotenv(override=True)
    
    config = Config(
        LLM_PROVIDER=os.getenv("LLM_PROVIDER", "mock"),
        LLM_API_KEY=os.getenv("LLM_API_KEY", ""),
        LLM_MODEL=os.getenv("LLM_MODEL", ""),
        TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        TELEGRAM_CHAT_ID=os.getenv("TELEGRAM_CHAT_ID", ""),
        EMAIL_ENABLED=os.getenv("EMAIL_ENABLED", "false").lower() == "true",
        SMTP_HOST=os.getenv("SMTP_HOST", ""),
        SMTP_PORT=int(os.getenv("SMTP_PORT", 587)),
        SMTP_USERNAME=os.getenv("SMTP_USERNAME", ""),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD", ""),
        EMAIL_TO=os.getenv("EMAIL_TO", ""),
        EMAIL_FROM=os.getenv("EMAIL_FROM", ""),
        TIMEZONE_OFFSET_HOURS=int(os.getenv("TIMEZONE_OFFSET_HOURS", 0)),
        MAX_NEWS_ITEMS=int(os.getenv("MAX_NEWS_ITEMS", 30)),
        SUMMARY_WORDS_MIN=int(os.getenv("SUMMARY_WORDS_MIN", 900)),
        SUMMARY_WORDS_MAX=int(os.getenv("SUMMARY_WORDS_MAX", 1100)),
        IDEA_COUNT=int(os.getenv("IDEA_COUNT", 10)),
        DRY_RUN=os.getenv("DRY_RUN", "false").lower() == "true",
        OUTPUT_DIR=os.getenv("OUTPUT_DIR", "output"),
        DATA_DIR=os.getenv("DATA_DIR", "data")
    )
    return config
