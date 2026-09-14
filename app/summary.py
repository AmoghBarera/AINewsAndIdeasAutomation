import os
import logging
from typing import List
from datetime import datetime, timezone
from app.models import NewsItem
from app.config import Config
from app.llm import generate_text

logger = logging.getLogger(__name__)

def generate_summary(filtered_items: List[NewsItem], config: Config) -> str:
    """Generate a daily summary from the top filtered news items."""
    
    # 1. Load the prompt template
    prompt_path = os.path.join("prompts", "summary.txt")
    if not os.path.exists(prompt_path):
        logger.error(f"Summary prompt template not found at {prompt_path}")
        return "Error: Summary prompt template missing."
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
        
    # Replace [DATE] placeholder in prompt or just pass it in user prompt
    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    # 2. Format the items into a text payload
    payload_lines = [f"DATE: {today_date}", "--- RAW NEWS ITEMS ---"]
    for i, item in enumerate(filtered_items):
        payload_lines.append(f"\nItem {i+1}:")
        payload_lines.append(f"Title: {item.title}")
        payload_lines.append(f"Source: {item.source}")
        payload_lines.append(f"URL: {item.url}")
        if item.summary:
            payload_lines.append(f"Summary: {item.summary}")
    
    user_prompt = "\n".join(payload_lines)
    
    # 3. First LLM Call
    logger.info("Generating initial summary...")
    summary = generate_text(
        prompt=user_prompt,
        system_prompt=system_prompt.replace("[DATE]", today_date),
        temperature=0.3,
        max_tokens=3000
    )
    
    # 4. Word count check
    word_count = len(summary.split())
    logger.info(f"Initial summary word count: {word_count}")
    
    if word_count < 800 or word_count > 1300:
        if config.LLM_PROVIDER.lower() != "mock":  # Don't retry in mock mode
            logger.info("Summary word count outside target range. Adjusting...")
            adjustment_instruction = ""
            if word_count < 800:
                adjustment_instruction = "The previous summary was too short. Please rewrite it, expanding on the details of each section based ONLY on the provided news items. Do NOT invent facts. Aim for exactly 900 to 1100 words."
            else:
                adjustment_instruction = "The previous summary was too long. Please rewrite it more concisely, aiming for exactly 900 to 1100 words. Keep all the sections intact."
                
            retry_prompt = user_prompt + f"\n\n--- PREVIOUS OUTPUT ---\n{summary}\n\n--- INSTRUCTION ---\n{adjustment_instruction}"
            
            new_summary = generate_text(
                prompt=retry_prompt,
                system_prompt=system_prompt.replace("[DATE]", today_date),
                temperature=0.2, # slightly lower for adjustment
                max_tokens=3000
            )
            
            new_word_count = len(new_summary.split())
            logger.info(f"Adjusted summary word count: {new_word_count}")
            
            # Use the new one if it's better or just fall back to whatever we got
            if 800 <= new_word_count <= 1300:
                summary = new_summary
            else:
                logger.warning("Second attempt also missed target word count. Using second attempt anyway.")
                summary = new_summary

    # 5. Save the summary
    output_dir = os.path.join(config.OUTPUT_DIR, "latest")
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "summary.md")
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(summary)
        
    logger.info(f"Summary generated and saved to {out_path}")
    return summary
