import logging
from app.config import load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    print("Daily Tech & AI Opportunity Brief")
    config = load_config()
    logging.info(f"Configuration loaded. Provider: {config.LLM_PROVIDER}")

if __name__ == "__main__":
    main()
