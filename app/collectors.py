import logging
import hashlib
import time
from datetime import datetime, timezone
import requests
import feedparser
from typing import List, Dict, Any, Optional
import xml.etree.ElementTree as ET

from app.models import NewsItem
from app.sources import load_sources, SourceConfig
from app.utils import get_current_utc_datetime

logger = logging.getLogger(__name__)

TIMEOUT = 15
MAX_RETRIES = 2
USER_AGENT = "DailyTechAndAIOpportunityBrief/1.0 (Python Bot)"

def generate_id(url: str, title: str) -> str:
    """Generate a stable ID based on URL or title."""
    unique_string = url if url else title
    return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

def fetch_with_retry(url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None) -> Optional[requests.Response]:
    """Fetch a URL with retries."""
    if headers is None:
        headers = {}
    if "User-Agent" not in headers:
        headers["User-Agent"] = USER_AGENT

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for {url}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
    return None

def collect_rss_sources(config: SourceConfig) -> List[NewsItem]:
    items = []
    if not config.rss:
        return items

    for source in config.rss:
        logger.info(f"Fetching RSS: {source.name} ({source.url})")
        # feedparser does not have a built-in strict timeout that works everywhere,
        # so we fetch with requests first, then parse.
        response = fetch_with_retry(source.url)
        if not response:
            logger.warning(f"Failed to fetch RSS: {source.name}")
            continue

        feed = feedparser.parse(response.content)
        if getattr(feed, 'bozo', 0) == 1 and not feed.entries:
            logger.warning(f"Failed to parse RSS or empty feed: {source.name}")
            continue

        for entry in feed.entries:
            title = entry.get("title", "")
            url = entry.get("link", "")
            if not title and not url:
                continue

            summary = entry.get("summary", entry.get("description", ""))
            
            # Convert published date to ISO
            published_at = ""
            if "published_parsed" in entry and entry.published_parsed:
                dt = datetime.fromtimestamp(time.mktime(entry.published_parsed), tz=timezone.utc)
                published_at = dt.isoformat()
            
            items.append(NewsItem(
                id=generate_id(url, title),
                title=title,
                url=url,
                source=source.name,
                summary=summary,
                published_at=published_at,
                score=0.0,
                metadata={"weight": source.weight}
            ))

    return items

def collect_hacker_news(config: SourceConfig) -> List[NewsItem]:
    items = []
    if not config.hacker_news:
        return items

    logger.info("Fetching Hacker News")
    hn_config = config.hacker_news
    
    for query in hn_config.queries:
        url = "http://hn.algolia.com/api/v1/search_by_date"
        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": hn_config.limit
        }
        
        response = fetch_with_retry(url, params=params)
        if not response:
            logger.warning(f"Failed to fetch HN for query: {query}")
            continue
            
        try:
            data = response.json()
            for hit in data.get("hits", []):
                title = hit.get("title", "")
                url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                if not title:
                    continue
                
                score = float(hit.get("points", 0))
                published_at = hit.get("created_at", "")
                
                items.append(NewsItem(
                    id=generate_id(url, title),
                    title=title,
                    url=url,
                    source="Hacker News",
                    summary="",
                    published_at=published_at,
                    score=score,
                    metadata={"query": query, "points": score, "weight": hn_config.weight}
                ))
        except ValueError as e:
            logger.warning(f"Failed to parse HN JSON: {e}")

    return items

def collect_reddit(config: SourceConfig) -> List[NewsItem]:
    items = []
    if not config.reddit:
        return items

    logger.info("Fetching Reddit")
    reddit_config = config.reddit
    
    for subreddit in reddit_config.subreddits:
        url = f"https://www.reddit.com/r/{subreddit}/top.json"
        params = {"t": "day", "limit": reddit_config.limit}
        
        response = fetch_with_retry(url, params=params)
        if not response:
            logger.warning(f"Failed to fetch Reddit r/{subreddit}")
            continue
            
        try:
            data = response.json()
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                title = post.get("title", "")
                url = post.get("url", "")
                if not title:
                    continue
                
                # Reddit URL fallback if it's a self post
                if not url.startswith("http"):
                    url = f"https://www.reddit.com{post.get('permalink', '')}"
                    
                score = float(post.get("score", 0))
                created_utc = post.get("created_utc", 0)
                published_at = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat() if created_utc else ""
                
                items.append(NewsItem(
                    id=generate_id(url, title),
                    title=title,
                    url=url,
                    source=f"Reddit (r/{subreddit})",
                    summary=post.get("selftext", ""),
                    published_at=published_at,
                    score=score,
                    metadata={"subreddit": subreddit, "score": score, "weight": reddit_config.weight}
                ))
        except ValueError as e:
            logger.warning(f"Failed to parse Reddit JSON: {e}")

    return items

def collect_arxiv(config: SourceConfig) -> List[NewsItem]:
    items = []
    if not config.arxiv:
        return items

    logger.info("Fetching arXiv")
    arxiv_config = config.arxiv
    
    # Construct query: cat:cs.AI OR cat:cs.LG ...
    query_parts = [f"cat:{cat}" for cat in arxiv_config.categories]
    search_query = "+OR+".join(query_parts)
    
    url = f"http://export.arxiv.org/api/query?search_query={search_query}&sortBy=submittedDate&sortOrder=desc&max_results={arxiv_config.limit}"
    
    response = fetch_with_retry(url)
    if not response:
        logger.warning("Failed to fetch arXiv")
        return items
        
    try:
        root = ET.fromstring(response.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns)
            title_text = title.text.replace('\\n', ' ').strip() if title is not None else ""
            
            link = entry.find("atom:id", ns)
            url_text = link.text if link is not None else ""
            
            summary = entry.find("atom:summary", ns)
            summary_text = summary.text.replace('\\n', ' ').strip() if summary is not None else ""
            
            published = entry.find("atom:published", ns)
            published_at = published.text if published is not None else ""
            
            if not title_text or not url_text:
                continue
                
            items.append(NewsItem(
                id=generate_id(url_text, title_text),
                title=title_text,
                url=url_text,
                source="arXiv",
                summary=summary_text,
                published_at=published_at,
                score=0.0,
                metadata={"weight": arxiv_config.weight}
            ))
    except ET.ParseError as e:
        logger.warning(f"Failed to parse arXiv XML: {e}")

    return items

def collect_all_sources(config: SourceConfig) -> List[NewsItem]:
    """Collects news items from all enabled sources."""
    all_items: List[NewsItem] = []
    
    if config.rss:
        try:
            all_items.extend(collect_rss_sources(config))
        except Exception as e:
            logger.warning(f"Failed to collect RSS sources: {e}")
        time.sleep(1)
        
    if config.hacker_news:
        try:
            all_items.extend(collect_hacker_news(config))
        except Exception as e:
            logger.warning(f"Failed to collect Hacker News: {e}")
        time.sleep(1)
        
    if config.reddit:
        try:
            all_items.extend(collect_reddit(config))
        except Exception as e:
            logger.warning(f"Failed to collect Reddit: {e}")
        time.sleep(1)
            
    if config.arxiv:
        try:
            all_items.extend(collect_arxiv(config))
        except Exception as e:
            logger.warning(f"Failed to collect arXiv: {e}")
        
    logger.info(f"Total raw items collected: {len(all_items)}")
    return all_items
