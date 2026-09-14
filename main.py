import logging
import sys
import os
import json
from dataclasses import asdict
from app.config import load_config
from app.sources import load_sources, get_enabled_sources
from app.collectors import collect_all_sources

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
        return

    if "--collect-only" in sys.argv:
        logging.info("Running in --collect-only mode")
        source_config = load_sources()
        items = collect_all_sources(source_config)
        
        output_dir = os.path.join(config.OUTPUT_DIR, "latest")
        os.makedirs(output_dir, exist_ok=True)
        raw_out_path = os.path.join(output_dir, "raw_items.json")
        
        # Convert items to dict for JSON serialization
        items_dict = [asdict(item) for item in items]
        with open(raw_out_path, "w", encoding="utf-8") as f:
            json.dump(items_dict, f, indent=4)
        
        logging.info(f"Collected {len(items)} items and saved to {raw_out_path}")
        return

if __name__ == "__main__":
    main()
