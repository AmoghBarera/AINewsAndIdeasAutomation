import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Set
import difflib

from app.models import NewsItem
from app.config import Config

KEYWORDS = [
    "ai", "artificial intelligence", "llm", "large language model",
    "agent", "autonomous", "startup", "funding", "regulation",
    "open source", "model", "transformer", "gpu", "robotics",
    "biotech", "quantum"
]

def parse_date(date_str: str) -> datetime:
    """Attempt to parse ISO date string, fallback to epoch."""
    if not date_str:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime.fromtimestamp(0, tz=timezone.utc)

def filter_recent_items(items: List[NewsItem], hours: int = 24) -> List[NewsItem]:
    """Keep items from the last specified hours."""
    recent_items = []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)

    for item in items:
        dt = parse_date(item.published_at)
        
        # If date is missing/invalid, check if engagement is high enough to keep
        if dt == datetime.fromtimestamp(0, tz=timezone.utc):
            if item.score > 20 or item.metadata.get("points", 0) > 50 or item.metadata.get("score", 0) > 100:
                recent_items.append(item)
        elif dt >= cutoff:
            recent_items.append(item)
            
    return recent_items

def normalize_title(title: str) -> str:
    """Normalize title for comparison."""
    return re.sub(r'[^a-z0-9]', '', title.lower())

def deduplicate_items(items: List[NewsItem]) -> List[NewsItem]:
    """Remove duplicate URLs and near-duplicate titles."""
    seen_urls: Set[str] = set()
    deduped_by_url = []

    # 1. Deduplicate by URL
    for item in items:
        if item.url and item.url not in seen_urls:
            seen_urls.add(item.url)
            deduped_by_url.append(item)

    # 2. Deduplicate by Title (keep highest score or first seen)
    # Sort by score so we keep the most engaged one
    deduped_by_url.sort(key=lambda x: x.score, reverse=True)
    
    final_items = []
    seen_titles: List[str] = []

    for item in deduped_by_url:
        norm_title = normalize_title(item.title)
        
        is_duplicate = False
        for seen_title in seen_titles:
            # Simple similarity check
            if len(norm_title) > 10 and len(seen_title) > 10:
                ratio = difflib.SequenceMatcher(None, norm_title, seen_title).ratio()
                if ratio > 0.85:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            seen_titles.append(norm_title)
            final_items.append(item)

    return final_items

def score_items(items: List[NewsItem]) -> List[NewsItem]:
    """Calculate and assign scores to items."""
    now = datetime.now(timezone.utc)
    
    for item in items:
        base_score = 0.0
        
        # 1. Recency
        dt = parse_date(item.published_at)
        if dt.year > 1970:
            age_hours = (now - dt).total_seconds() / 3600
            if age_hours <= 6:
                base_score += 10
            elif age_hours <= 12:
                base_score += 7
            elif age_hours <= 24:
                base_score += 4
                
        # 2. Source Weight
        weight = item.metadata.get("weight", 1)
        base_score += (weight * 2)
        
        # 3. Keyword Relevance
        title_lower = item.title.lower()
        summary_lower = item.summary.lower() if item.summary else ""
        combined = f"{title_lower} {summary_lower}"
        
        for kw in KEYWORDS:
            if kw in combined:
                base_score += 5
                break # Only add keyword bonus once to prevent keyword stuffing
                
        # 4. Engagement
        hn_points = float(item.metadata.get("points", 0))
        if hn_points > 0:
            hn_bonus = min(hn_points / 10.0, 20.0) # Cap at +20
            base_score += hn_bonus
            
        reddit_score = float(item.metadata.get("score", 0))
        if reddit_score > 0 and item.source.startswith("Reddit"):
            reddit_bonus = min(reddit_score / 25.0, 15.0) # Cap at +15
            base_score += reddit_bonus
            
        item.score = base_score
        
    return items

def rank_items(items: List[NewsItem], max_items: int = 30) -> List[NewsItem]:
    """Sort by score and enforce source diversity."""
    items.sort(key=lambda x: x.score, reverse=True)
    
    # Enforce diversity: try not to have more than max_per_source from a single source
    # If we run out of diverse items, we just take the best remaining
    max_per_source = max(3, max_items // 4)
    
    source_counts: Dict[str, int] = {}
    ranked = []
    skipped = []
    
    for item in items:
        src = item.source
        if source_counts.get(src, 0) < max_per_source:
            ranked.append(item)
            source_counts[src] = source_counts.get(src, 0) + 1
        else:
            skipped.append(item)
            
        if len(ranked) >= max_items:
            break
            
    # If we didn't fill the quota, add skipped items back
    while len(ranked) < max_items and skipped:
        ranked.append(skipped.pop(0))
        
    return ranked

def filter_and_rank(items: List[NewsItem], config: Config) -> List[NewsItem]:
    """Pipeline to turn raw items into the final ranked list."""
    filtered = filter_recent_items(items, hours=24)
    deduped = deduplicate_items(filtered)
    scored = score_items(deduped)
    ranked = rank_items(scored, max_items=config.MAX_NEWS_ITEMS)
    return ranked
