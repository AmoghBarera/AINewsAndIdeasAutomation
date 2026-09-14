import json
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class RSSSource:
    name: str
    url: str
    weight: int

@dataclass
class HackerNewsSource:
    queries: List[str]
    limit: int
    weight: int

@dataclass
class RedditSource:
    subreddits: List[str]
    limit: int
    weight: int

@dataclass
class ArxivSource:
    categories: List[str]
    limit: int
    weight: int

@dataclass
class SourceConfig:
    rss: List[RSSSource]
    hacker_news: Optional[HackerNewsSource]
    reddit: Optional[RedditSource]
    arxiv: Optional[ArxivSource]

def load_sources(filepath: str = "sources.json") -> SourceConfig:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Source configuration file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filepath}: {e}")

    rss_sources = []
    for rss_item in data.get("rss", []):
        if rss_item.get("enabled", False):
            rss_sources.append(RSSSource(
                name=rss_item.get("name", ""),
                url=rss_item.get("url", ""),
                weight=rss_item.get("weight", 1)
            ))

    hn_data = data.get("hacker_news", {})
    hn_source = None
    if hn_data.get("enabled", False):
        hn_source = HackerNewsSource(
            queries=hn_data.get("queries", []),
            limit=hn_data.get("limit", 30),
            weight=hn_data.get("weight", 1)
        )

    reddit_data = data.get("reddit", {})
    reddit_source = None
    if reddit_data.get("enabled", False):
        reddit_source = RedditSource(
            subreddits=reddit_data.get("subreddits", []),
            limit=reddit_data.get("limit", 15),
            weight=reddit_data.get("weight", 1)
        )

    arxiv_data = data.get("arxiv", {})
    arxiv_source = None
    if arxiv_data.get("enabled", False):
        arxiv_source = ArxivSource(
            categories=arxiv_data.get("categories", []),
            limit=arxiv_data.get("limit", 20),
            weight=arxiv_data.get("weight", 1)
        )

    return SourceConfig(
        rss=rss_sources,
        hacker_news=hn_source,
        reddit=reddit_source,
        arxiv=arxiv_source
    )

def get_enabled_sources(filepath: str = "sources.json") -> Dict[str, Any]:
    """Returns a simplified dictionary of enabled sources."""
    config = load_sources(filepath)
    enabled = {
        "rss_count": len(config.rss),
        "hacker_news": config.hacker_news is not None,
        "reddit": config.reddit is not None,
        "arxiv": config.arxiv is not None
    }
    
    total_enabled_types = sum([
        1 if enabled["rss_count"] > 0 else 0,
        1 if enabled["hacker_news"] else 0,
        1 if enabled["reddit"] else 0,
        1 if enabled["arxiv"] else 0
    ])
    
    enabled["total_enabled_types"] = total_enabled_types
    enabled["total_rss_feeds"] = enabled["rss_count"]
    return enabled
