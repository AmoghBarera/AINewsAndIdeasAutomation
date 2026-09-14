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
    preview = truncate_text(prompt, 100)
    return (
        "### MOCK LLM OUTPUT ###\n\n"
        "This is a mocked response because no LLM API key was provided or 'mock' was explicitly selected.\n\n"
        "**Received System Prompt:**\n"
        f"{system_prompt or 'None'}\n\n"
        "**Received User Prompt (Preview):**\n"
        f"{preview}\n\n"
        "**Mock Tech Summary:**\n"
        "AI continues to advance. New LLMs are being released with better reasoning capabilities.\n"
        "Startups are finding niches in vertical SaaS using these models.\n\n"
        "**Mock Idea:**\n"
        "1. ComplianceAgent: An AI tool that automatically checks SOC2 compliance documents against live AWS configurations."
    )

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

def generate_text(
    prompt: str,
    system_prompt: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 2500
) -> str:
    """Generate text using the configured LLM provider."""
    config = load_config()
    
    provider = (provider or config.LLM_PROVIDER or "mock").lower()
    api_key = config.LLM_API_KEY
    model = model or config.LLM_MODEL
    
    # Fallback to mock if API key is missing and provider is not mock
    if provider != "mock" and not api_key:
        logger.warning(f"No API key provided for {provider}. Falling back to 'mock' provider.")
        provider = "mock"
        
    logger.info(f"Generating text using provider: {provider}, model: {model or 'default'}")
    
    retries = 1
    for attempt in range(retries + 1):
        try:
            if provider == "gemini":
                return _gemini_provider(prompt, system_prompt, api_key, model, temperature, max_tokens)
            elif provider == "groq":
                return _groq_provider(prompt, system_prompt, api_key, model, temperature, max_tokens)
            elif provider == "openrouter":
                return _openrouter_provider(prompt, system_prompt, api_key, model, temperature, max_tokens)
            elif provider == "mock":
                return _mock_provider(prompt, system_prompt)
            else:
                logger.warning(f"Unknown provider: {provider}. Falling back to 'mock'.")
                return _mock_provider(prompt, system_prompt)
                
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            # Don't retry on auth errors or bad requests
            if status_code in (400, 401, 403, 404):
                logger.error(f"Client error from {provider} API: {e}")
                return f"Error: Failed to generate text due to client error ({status_code})."
                
            logger.warning(f"Transient error from {provider} (Attempt {attempt+1}): {e}")
            if attempt < retries:
                time.sleep(5)
            else:
                logger.error(f"Failed to generate text after retries.")
                return f"Error: Failed to generate text after retries."
        except Exception as e:
            logger.error(f"Unexpected error generating text with {provider}: {e}")
            return f"Error: An unexpected error occurred."
