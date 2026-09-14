# Daily Tech & AI Opportunity Brief

A fully free, automated daily script that gathers tech and AI news from free sources (RSS/web), summarizes the most important developments, and generates 10 high-quality, non-generic, monetizable startup ideas inspired by the news. The output is a Markdown report, optionally delivered via Telegram or email.

## Setup Instructions

1. Ensure you have Python 3.11+ installed.
2. Clone the repository.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
5. Configure your environment variables in `.env`.

## Environment Variables

- `LLM_PROVIDER`: The LLM to use (`mock`, `gemini`, `groq`). Default is `mock`.
- `LLM_API_KEY`: API key for the selected provider.
- `LLM_MODEL`: The specific model to use (e.g., `gemini-1.5-pro`).
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`: Config for Telegram delivery.
- `EMAIL_ENABLED`, `SMTP_*`: Config for Email delivery.
- `MAX_NEWS_ITEMS`: Max number of items to process daily.
- `SUMMARY_WORDS_MIN`, `SUMMARY_WORDS_MAX`: Target word count for the summary.
- `IDEA_COUNT`: Number of ideas to generate (default 10).
- `DRY_RUN`: If true, disables sending notifications and writing outputs.
- `OUTPUT_DIR`, `DATA_DIR`: Directories for outputs and internal JSON state.

## How to run local dry run

Run the application locally. It defaults to the mock LLM if keys are omitted.

```bash
python main.py
```

## GitHub Actions Automation

This repository includes a GitHub Actions workflow (`.github/workflows/daily-brief.yml`) that runs the pipeline on a schedule.

**Note on Timezones:**
The GitHub Actions cron scheduler operates in **UTC** time. 
For example, the default `0 9 * * *` runs at 9:00 AM UTC. If you want the brief delivered at 9:00 AM in your local timezone, you must convert your local time to UTC and update the cron string accordingly.
