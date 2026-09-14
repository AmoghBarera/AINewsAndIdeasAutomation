import logging
import requests
import time
from typing import Optional, Dict, Any
from app.config import load_config
from app.utils import truncate_text

logger = logging.getLogger(__name__)

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"
DEFAULT_GROQ_MODEL = "llama3-8b-8192"

def _mock_provider(prompt: str, system_prompt: Optional[str]) -> str:
    """Mock LLM response for local testing."""
    import datetime
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    
    # Check if this is the ideas prompt
    if system_prompt and "10 unique" in system_prompt.lower():
        return """### 1. ComplianceAgent API
An AI tool that automatically checks SOC2 compliance documents against live AWS configurations.

Problem:
Companies spend hundreds of hours manually verifying that their cloud infrastructure matches their written compliance policies.

Customer:
B2B: Security/Compliance Officers at mid-market SaaS companies.

Solution:
A local-first AI agent that reads policy PDFs and queries AWS APIs to verify compliance without sending sensitive data to external LLMs.

Why now:
Recent open-source models (like Llama 3) allow for secure, on-premise document reasoning.

Monetization:
$500/month SaaS subscription.

First 10 customers:
Cold outreach to CTOs of YC startups that recently announced their seed rounds and need to get SOC2.

Uniqueness angle:
Local-first execution ensures zero data leakage, solving a major blocker for enterprises.

Closest existing alternative:
Vanta or Drata (which are generic and rely on manual evidence collection for edge cases).

Why it is different:
We use agentic workflows to handle the edge cases that Vanta cannot automate.

News trend that inspired it:
Recent releases of highly capable small open-source models for enterprise security.

### 2. AutoTender
An AI workflow automation tool that drafts public procurement bids for construction firms.

Problem:
Construction firms miss out on lucrative government contracts because responding to 500-page RFPs takes weeks.

Customer:
B2B: Mid-sized commercial construction firms.

Solution:
A customized RAG system that ingests past winning bids and automatically drafts compliant responses to new government RFPs.

Why now:
Context windows in models like Claude 3 or Gemini 1.5 have expanded enough to ingest entire historical bid libraries at once.

Monetization:
Per-bid fee ($1000) or high-ticket SaaS ($2k/mo).

First 10 customers:
Scraping government portals for recent contract winners and cold-emailing their VP of Sales.

Uniqueness angle:
Domain-specific fine-tuning on construction terminology and legal jargon.

Closest existing alternative:
Generic AI writing tools (ChatGPT) or expensive proposal consultants.

Why it is different:
Integrated directly into the procurement databases with deep domain-specific retrieval.

News trend that inspired it:
The expansion of LLM context windows to millions of tokens.

### 3. GridPredict
A predictive maintenance platform for aging municipal water infrastructure using edge AI.

Problem:
Municipalities lose millions of gallons of water to undetected pipe leaks before they become catastrophic failures.

Customer:
B2G: Local municipal water departments.

Solution:
Low-cost acoustic sensors deployed on pipes running edge AI to detect anomalies and predict leaks before they burst.

Why now:
Hardware optimized for edge AI is now cheap enough to deploy at scale, and models can run locally without cloud dependency.

Monetization:
Hardware + Software subscription (SaaS + IoT).

First 10 customers:
Local city councils in regions experiencing severe drought.

Uniqueness angle:
Hardware-software integration creating a proprietary data moat.

Closest existing alternative:
Manual acoustic surveys done once every 5 years.

Why it is different:
Continuous, real-time monitoring at a fraction of the manual labor cost.

News trend that inspired it:
The rise of "small language models" and edge AI hardware optimized for low power."""

    # Check if this is the critic prompt
    if system_prompt and "venture capitalist" in system_prompt.lower():
        # Just extract the raw ideas and append the mock note
        raw = prompt.replace("--- RAW IDEAS TO REVIEW AND IMPROVE ---\n\n", "")
        return raw + "\n\n*(Critic mode is mocked.)*"

    return f"""# Daily Tech & AI Brief — {today}

## Big Picture
The tech industry is seeing rapid advancements in AI models and agentic frameworks. Startups are increasingly focusing on vertical applications rather than foundational models, seeking product-market fit in specialized niches. Meanwhile, open-source communities are releasing tools that rival proprietary systems in specific benchmarks.

## Top Developments
1. Several major tech firms announced updates to their foundational language models, citing improvements in reasoning and context windows.
2. A new wave of AI startups secured funding rounds, emphasizing the shift toward applied AI in healthcare and finance.

## Models, Products, and Launches
- **ComplianceAgent**: A new tool that automatically checks SOC2 compliance documents against live AWS configurations.
- **DataStream Pro**: A framework for ingesting real-time data into vector databases for RAG applications.

## Research and Breakthroughs
- A recent paper demonstrated a novel approach to reducing hallucination rates in LLMs by 30% using verifiable fact-checking loops.
- Researchers open-sourced a new benchmark for evaluating the safety of autonomous agents.

## Business, Funding, and Regulation
- A prominent AI safety startup raised $50M in Series B funding.
- Regulators in the EU published new guidelines on data privacy concerning generative AI models.

## Open Source and Developer Tools
- **AgentKit**: A new open-source library for building multi-agent systems gained massive traction on GitHub.
- Developers praised a new fast inference engine for running large models on consumer GPUs.

## What To Watch
1. The ongoing debate over copyright and training data usage.
2. The rise of "small language models" optimized for edge devices.
3. Increasing regulatory scrutiny on AI agents that can execute financial transactions."""

def _gemini_provider(prompt: str, system_prompt: Optional[str], api_key: str, model: str, temperature: float, max_tokens: int) -> str:
    if not model:
        model = DEFAULT_GEMINI_MODEL
        
    url = GEMINI_API_URL.format(model=model, api_key=api_key)
    
    contents = []
    if system_prompt:
        contents.append({"role": "user", "parts": [{"text": f"System Instruction: {system_prompt}"}]})
        contents.append({"role": "model", "parts": [{"text": "Understood."}]})
    
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    
    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        logger.error(f"Failed to parse Gemini response: {data}")
        raise ValueError("Invalid Gemini response format") from e

def _groq_provider(prompt: str, system_prompt: Optional[str], api_key: str, model: str, temperature: float, max_tokens: int) -> str:
    if not model:
        model = DEFAULT_GROQ_MODEL
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        logger.error(f"Failed to parse Groq response: {data}")
        raise ValueError("Invalid Groq response format") from e

def _openrouter_provider(prompt: str, system_prompt: Optional[str], api_key: str, model: str, temperature: float, max_tokens: int) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model or "openrouter/auto",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        logger.error(f"Failed to parse OpenRouter response: {data}")
        raise ValueError("Invalid OpenRouter response format") from e

LLM_CHAIN = [
    {"provider": "gemini", "model": "gemini-3.7-flash"},
    {"provider": "gemini", "model": "gemini-3.1-pro"},
    {"provider": "groq", "model": "llama3-70b-8192"},
]

def generate_text(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 2500
) -> str:
    """Generate text using the configured LLM provider fallback chain."""
    config = load_config()
    
    for step_index, step in enumerate(LLM_CHAIN):
        provider = step["provider"]
        model = step["model"]
        
        # Check for API key
        api_key = None
        if provider == "gemini":
            api_key = config.GEMINI_API_KEY
        elif provider == "groq":
            api_key = config.GROQ_API_KEY
            
        if not api_key:
            logger.warning(f"Step {step_index + 1}: Skipping {provider} ({model}) - missing API key in environment.")
            continue
            
        logger.info(f"Step {step_index + 1}: Attempting generation with {provider} ({model})...")
        
        try:
            if provider == "gemini":
                return _gemini_provider(prompt, system_prompt, api_key, model, temperature, max_tokens)
            elif provider == "groq":
                return _groq_provider(prompt, system_prompt, api_key, model, temperature, max_tokens)
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            logger.warning(f"Model {model} failed with HTTP {status_code}: {e}. Trying next in chain...")
        except requests.exceptions.Timeout as e:
            logger.warning(f"Model {model} timed out: {e}. Trying next in chain...")
        except Exception as e:
            logger.warning(f"Model {model} encountered an unexpected error: {e}. Trying next in chain...")
            
    # If the entire chain fails or is skipped, fallback to mock if possible
    logger.error("All models in the LLM chain failed or lacked API keys.")
    logger.info("Falling back to 'mock' provider as a last resort.")
    return _mock_provider(prompt, system_prompt)
