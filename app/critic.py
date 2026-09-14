import os
import logging
from app.config import Config
from app.llm import generate_text

logger = logging.getLogger(__name__)

def improve_ideas(raw_ideas: str, config: Config) -> str:
    """Pass generated ideas through a critic to improve uniqueness and viability."""
    
    prompt_path = os.path.join("prompts", "critic.txt")
    if not os.path.exists(prompt_path):
        logger.error(f"Critic prompt template not found at {prompt_path}")
        return raw_ideas
        
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
        
    user_prompt = f"--- RAW IDEAS TO REVIEW AND IMPROVE ---\n\n{raw_ideas}"
    
    logger.info("Running idea critic...")
    try:
        improved_ideas = generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.4,
            max_tokens=4000
        )
        return improved_ideas
    except Exception as e:
        logger.error(f"Critic generation failed: {e}. Returning original ideas.")
        return raw_ideas
