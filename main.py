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
    
    # Setup file logging
    os.makedirs(os.path.join(config.OUTPUT_DIR, "latest"), exist_ok=True)
    log_file = os.path.join(config.OUTPUT_DIR, "latest", "run.log")
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(file_handler)
    
    logging.info("==========================================")
    logging.info("Starting new run of Daily Tech & AI Brief")
    
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

    if "--help" in sys.argv:
        print("Usage: python main.py [OPTIONS]")
        print("Options:")
        print("  --help              Show this message and exit")
        print("  --collect-only      Run only the collection phase")
        print("  --filter-only       Run collection and filtering phases")
        print("  --summary-only      Run collection, filtering, and summary phases")
        print("  --ideas-only        Run collection, filtering, summary, and idea phases")
        print("  --build-report-only Build report from existing files")
        print("  --deliver-only      Deliver an existing report via Email")
        print("  --send-test-email   Send a test email to verify SMTP settings")
        print("  --full              Run the full pipeline (default)")
        print("  --dry-run           Do not send emails (logs instead)")
        print("  --no-deliver        Run everything but skip email delivery")
        print("  --llm-test          Test the LLM connection")
        return

    if "--send-test-email" in sys.argv:
        from app.delivery import send_email_message
        logging.info("Running Email delivery test...")
        test_text = "# Test Email\n\nThis is a test of the Daily Tech & AI Brief email delivery system."
        test_path = "tests/test_smoke.py" # just a dummy path to test attachment if needed, or non-existent
        success = send_email_message(test_text, test_path, config)
        if success:
            logging.info("Test email sent successfully!")
        else:
            logging.error("Test email failed. Check your SMTP credentials and connection.")
        return

    if "--dry-run" in sys.argv:
        config.DRY_RUN = True
        logging.info("DRY_RUN enabled via CLI.")

    # Determine which phases to run
    phase_flags = {"--collect-only", "--filter-only", "--summary-only", "--ideas-only", "--build-report-only", "--deliver-only", "--full"}
    has_phase_flag = any(flag in sys.argv for flag in phase_flags)
    
    # If no phase flag is provided, or if --full is provided, run everything
    run_full = not has_phase_flag or "--full" in sys.argv
    
    run_collection = run_full or "--collect-only" in sys.argv or "--filter-only" in sys.argv or "--summary-only" in sys.argv or "--ideas-only" in sys.argv
    run_filter = run_full or "--filter-only" in sys.argv or "--summary-only" in sys.argv or "--ideas-only" in sys.argv
    run_summary = run_full or "--summary-only" in sys.argv
    run_ideas = run_full or "--ideas-only" in sys.argv
    run_report = run_full or "--build-report-only" in sys.argv
    run_delivery = (run_full or "--deliver-only" in sys.argv) and "--no-deliver" not in sys.argv

    # Shared state for the final report
    final_report = None
    summary = ""
    ideas_text = ""
    
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
            
            llm_failed = False
            
            if run_summary:
                logging.info("Running summary generation phase...")
                try:
                    summary = generate_summary(filtered_items, config)
                    logging.info(f"Summary generated successfully. Length: {len(summary)} chars.")
                except Exception as e:
                    logging.error(f"Summary generation failed: {e}")
                    summary = "LLM unavailable: automated fallback report only. Summary could not be generated."
                    llm_failed = True
                
            if run_ideas:
                from app.history import get_previous_idea_titles, append_new_ideas_to_history
                logging.info("Running idea generation phase...")
                if not llm_failed:
                    try:
                        previous_ideas = get_previous_idea_titles(limit=50)
                        ideas_text = generate_ideas(filtered_items, config, previous_ideas=previous_ideas)
                        logging.info(f"Ideas generated successfully. Length: {len(ideas_text)} chars.")
                        
                        # Append to history
                        append_new_ideas_to_history(ideas_text)
                    except Exception as e:
                        logging.error(f"Idea generation failed: {e}")
                        ideas_text = "LLM unavailable: automated fallback report only. Ideas could not be generated."
                        llm_failed = True
                else:
                    ideas_text = "LLM unavailable: automated fallback report only. Ideas could not be generated."
                
            if run_report:
                from app.report import build_final_report
                logging.info("Building final report...")
                
                if llm_failed:
                    # Create a basic report with just the titles of top items
                    top_items_list = "\n".join([f"- [{item.title}]({item.url}) ({item.source_name})" for item in filtered_items[:10]])
                    summary = "LLM unavailable: automated fallback report only.\n\n### Top News Items Today:\n" + top_items_list
                    ideas_text = "*(Skipped due to LLM failure)*"
                    
                final_report = build_final_report(summary, ideas_text, config)
                logging.info(f"Final report generated. Length: {len(final_report)} chars.")
                print("\n--- FINAL REPORT (PREVIEW) ---")
                print(final_report[:500] + "...\n[Truncated for console]")
                print("------------------------------\n")
                
    if run_delivery:
        from app.delivery import deliver_report
        
        latest_report_path = os.path.join(config.OUTPUT_DIR, "latest", "final_report.md")
        try:
            status = deliver_report(latest_report_path, config)
            logging.info(f"Delivery status: {status}")
        except Exception as e:
            logging.error(f"Delivery encountered an unexpected error: {e}")

if __name__ == "__main__":
    main()

