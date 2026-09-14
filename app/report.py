import os
import shutil
from datetime import datetime, timezone
import logging
from app.config import Config

logger = logging.getLogger(__name__)

def build_final_report(summary_markdown: str, ideas_markdown: str, config: Config) -> str:
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    timestamp_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # Clean up markdown headers if they repeat the main title
    summary_clean = summary_markdown.replace(f"# Daily Tech & AI Brief — {today_str}", "").strip()
    
    report_lines = [
        f"# Daily Tech & AI Opportunity Brief — {today_str}",
        "",
        f"Generated at: {timestamp_str}",
        "",
        "---",
        "",
        "## Part 1: Technology and AI Summary",
        "",
        summary_clean,
        "",
        "---",
        "",
        "## Part 2: 10 Monetizable Opportunity Ideas",
        "",
        ideas_markdown
    ]
    
    final_report = "\n".join(report_lines)
    
    # Save to output/latest
    latest_dir = os.path.join(config.OUTPUT_DIR, "latest")
    os.makedirs(latest_dir, exist_ok=True)
    latest_report_path = os.path.join(latest_dir, "final_report.md")
    
    with open(latest_report_path, "w", encoding="utf-8") as f:
        f.write(final_report)
        
    logger.info(f"Final report saved to {latest_report_path}")
    
    # Also save to output/YYYY-MM-DD and copy all artifacts
    daily_dir = os.path.join(config.OUTPUT_DIR, today_str)
    os.makedirs(daily_dir, exist_ok=True)
    daily_report_path = os.path.join(daily_dir, "final_report.md")
    
    with open(daily_report_path, "w", encoding="utf-8") as f:
        f.write(final_report)
        
    logger.info(f"Final report saved to {daily_report_path}")
    
    # Copy other artifacts to the daily folder
    artifacts = ["raw_items.json", "filtered_items.json", "summary.md", "ideas.md"]
    for artifact in artifacts:
        src = os.path.join(latest_dir, artifact)
        dst = os.path.join(daily_dir, artifact)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            
    logger.info(f"Copied pipeline artifacts to {daily_dir}")
    
    return final_report
