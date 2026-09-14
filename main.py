import logging
from app.config import load_config
from app.sources import get_enabled_sources

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    print("Daily Tech & AI Opportunity Brief")
    config = load_config()
    logging.info(f"Configuration loaded. Provider: {config.LLM_PROVIDER}")
    
    try:
        sources_info = get_enabled_sources()
        logging.info(f"Sources loaded. Active feeds/types: {sources_info['total_rss_feeds']} RSS, "
                     f"HN: {sources_info['hacker_news']}, Reddit: {sources_info['reddit']}, "
                     f"Arxiv: {sources_info['arxiv']}")
    except Exception as e:
        logging.error(f"Failed to load sources: {e}")

if __name__ == "__main__":
    main()
