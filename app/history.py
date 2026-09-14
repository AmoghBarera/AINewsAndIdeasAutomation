import os
import json
import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.config import load_config

logger = logging.getLogger(__name__)

def get_history_file_path() -> str:
    config = load_config()
    os.makedirs(config.DATA_DIR, exist_ok=True)
    return os.path.join(config.DATA_DIR, "ideas_history.json")

def load_idea_history() -> List[Dict[str, Any]]:
    """Load the historical ideas from JSON."""
    file_path = get_history_file_path()
    if not os.path.exists(file_path):   
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Error decoding {file_path}. Returning empty history.")
        return []
    except Exception as e:
        logger.error(f"Error loading history: {e}")
        return []

def save_idea_history(history: List[Dict[str, Any]]):
    """Save the idea history to JSON, keeping the last 300 entries."""
    file_path = get_history_file_path()
    
    # Keep only the last 300 ideas
    history = history[-300:]
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
        logger.info(f"Saved {len(history)} ideas to history.")
    except Exception as e:
        logger.error(f"Failed to save idea history: {e}")

def extract_idea_titles(final_ideas_markdown: str) -> List[Dict[str, str]]:
    """Extract titles and pitches from the generated markdown ideas."""
    extracted = []
    
    # Matches lines like "### 1. Idea Name"
    # and tries to capture the next non-empty line as the pitch.
    lines = final_ideas_markdown.strip().split("\n")
    
    current_title = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        # Look for the heading
        if line.startswith("### ") and re.match(r'^###\s*\d+\.\s*(.+)', line):
            match = re.match(r'^###\s*\d+\.\s*(.+)', line)
            if match:
                current_title = match.group(1).strip()
                
                # Find the pitch (the next non-empty line that isn't a heading or label)
                pitch = ""
                for j in range(i + 1, min(i + 4, len(lines))):
                    next_line = lines[j].strip()
                    if next_line and not next_line.startswith("Problem:") and not next_line.startswith("###"):
                        pitch = next_line
                        break
                
                extracted.append({
                    "title": current_title,
                    "pitch": pitch
                })
                current_title = None
                
    return extracted

def append_new_ideas_to_history(final_ideas_markdown: str):
    """Parse the new ideas and append them to the history JSON."""
    history = load_idea_history()
    new_ideas = extract_idea_titles(final_ideas_markdown)
    
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    for idea in new_ideas:
        history.append({
            "date": today_str,
            "title": idea["title"],
            "pitch": idea["pitch"],
            "keywords": [] # Optional extraction later
        })
        
    if new_ideas:
        save_idea_history(history)
    else:
        logger.warning("No valid ideas parsed to add to history.")

def get_previous_idea_titles(limit: int = 50) -> List[str]:
    """Return a list of previous idea titles to avoid repetition."""
    history = load_idea_history()
    
    # Get the latest 'limit' ideas
    recent_history = history[-limit:] if limit > 0 else history
    
    return [item.get("title", "") for item in recent_history if item.get("title")]
