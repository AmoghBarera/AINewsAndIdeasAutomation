import os
import logging
from typing import List
from app.models import NewsItem
from app.config import Config
from app.llm import generate_text

logger = logging.getLogger(__name__)

def generate_ideas(filtered_items: List[NewsItem], config: Config, previous_ideas: List[str] = None) -> str:
    """Generate startup ideas based on the latest news."""
    
    if previous_ideas is None:
        previous_ideas = []
        
    prompt_path = os.path.join("prompts", "ideas.txt")
    if not os.path.exists(prompt_path):
        logger.error(f"Ideas prompt template not found at {prompt_path}")
        return "Error: Ideas prompt template missing."
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
        
    # Format the items into a concise context payload
    payload_lines = ["--- RECENT NEWS TRENDS ---"]
    for i, item in enumerate(filtered_items[:15]):  # Top 15 to keep context focused
        payload_lines.append(f"- {item.title}")
        if item.summary:
            # Add a brief snippet of the summary
            payload_lines.append(f"  ({item.summary[:150]}...)")
            
    if previous_ideas:
        payload_lines.append("\n--- PREVIOUS IDEAS (DO NOT REPEAT) ---")
        for idea in previous_ideas[:20]:
            payload_lines.append(f"- {idea}")
            
    user_prompt = "\n".join(payload_lines)
    
    logger.info("Generating ideas...")
    ideas_text = generate_text(
        prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.8,
        max_tokens=4000
    )
    
    # Save the output
    output_dir = os.path.join(config.OUTPUT_DIR, "latest")
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "ideas.md")
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(ideas_text)
        
    logger.info(f"Ideas generated and saved to {out_path}")
    return ideas_text
