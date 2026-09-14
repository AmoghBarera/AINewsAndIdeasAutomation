import logging
import sys
import os
import json
from dataclasses import asdict
from app.config import load_config
from app.sources import load_sources, get_enabled_sources
from app.collectors import collect_all_sources
from app.filters import filter_and_rank
from app.llm import generate_text
from app.summary import generate_summary
from app.ideas import generate_ideas

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    print("Daily Tech & AI Opportunity Brief")
    config = load_config()
    logging.info(f"Configuration loaded. Provider: {config.LLM_PROVIDER}")
    
    if "--llm-test" in sys.argv:
        logging.info("Running LLM test...")
        test_prompt = "Write a 3-sentence summary of the latest AI trends."
        test_system = "You are a helpful AI assistant."
        result = generate_text(prompt=test_prompt, system_prompt=test_system)
        print("\n--- LLM TEST RESULT ---")
        print(result)
        print("-----------------------\n")
        return

    try:
        sources_info = get_enabled_sources()
        logging.info(f"Sources loaded. Active feeds/types: {sources_info['total_rss_feeds']} RSS, "
                     f"HN: {sources_info['hacker_news']}, Reddit: {sources_info['reddit']}, "
                     f"Arxiv: {sources_info['arxiv']}")
    except Exception as e:
        logging.error(f"Failed to load sources: {e}")
        return

    run_collection = "--collect-only" in sys.argv or "--filter-only" in sys.argv or "--summary-only" in sys.argv or "--ideas-only" in sys.argv
    run_filter = "--filter-only" in sys.argv or "--summary-only" in sys.argv or "--ideas-only" in sys.argv
    run_summary = "--summary-only" in sys.argv
    run_ideas = "--ideas-only" in sys.argv

    if run_collection:
        logging.info("Running collection phase...")
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
        
        if run_filter:
            logging.info("Running filtering phase...")
            filtered_items = filter_and_rank(items, config)
            filtered_out_path = os.path.join(output_dir, "filtered_items.json")
            
            filtered_dict = [asdict(item) for item in filtered_items]
            with open(filtered_out_path, "w", encoding="utf-8") as f:
                json.dump(filtered_dict, f, indent=4)
            
            logging.info(f"Filtered and ranked down to {len(filtered_items)} items. Saved to {filtered_out_path}")
            
            if run_summary:
                logging.info("Running summary generation phase...")
                summary = generate_summary(filtered_items, config)
                logging.info(f"Summary generated successfully. Length: {len(summary)} chars.")
                print("\n--- GENERATED SUMMARY ---")
                print(summary[:500] + "...\n[Truncated for console]")
                print("-------------------------\n")
                
            if run_ideas:
                from app.history import get_previous_idea_titles, append_new_ideas_to_history
                logging.info("Running idea generation phase...")
                previous_ideas = get_previous_idea_titles(limit=50)
                ideas_text = generate_ideas(filtered_items, config, previous_ideas=previous_ideas)
                logging.info(f"Ideas generated successfully. Length: {len(ideas_text)} chars.")
                
                # Append to history
                append_new_ideas_to_history(ideas_text)
                
                print("\n--- GENERATED IDEAS ---")
                print(ideas_text[:500] + "...\n[Truncated for console]")
                print("-----------------------\n")
                
        return

if __name__ == "__main__":
    main()

