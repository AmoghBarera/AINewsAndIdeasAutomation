import json
import os
import re
from datetime import datetime, timezone

def get_current_utc_datetime() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)

def format_date_yyyy_mm_dd(dt: datetime) -> str:
    """Format a datetime object to YYYY-MM-DD string."""
    return dt.strftime("%Y-%m-%d")

def safe_read_json(filepath: str, default: any = None) -> any:
    """Safely read a JSON file, returning a default value if it doesn't exist."""
    if default is None:
        default = {}
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default

def safe_write_json(filepath: str, data: any) -> bool:
    """Safely write data to a JSON file."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True
    except IOError:
        return False

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to a maximum length safely."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."

def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in a string."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()
