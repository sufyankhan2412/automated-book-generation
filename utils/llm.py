"""
LLM abstraction — supports Google Gemini, OpenAI, and Groq.
Returns a LangChain chat model based on config.
Includes a retry wrapper to handle rate limits gracefully.
"""

import time
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
import config


# Max retries and backoff for rate limits
MAX_RETRIES = 5
RETRY_BASE_DELAY = 30  # seconds


def get_llm() -> BaseChatModel:
    """Return a configured LangChain chat model."""
    provider = config.LLM_PROVIDER

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not config.GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY must be set in .env")
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            google_api_key=config.GOOGLE_API_KEY,
            temperature=0.7,
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY must be set in .env")
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=config.OPENAI_API_KEY,
            temperature=0.7,
        )

    elif provider == "groq":
        from langchain_groq import ChatGroq

        if not config.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY must be set in .env")
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=config.GROQ_API_KEY,
            temperature=0.7,
            max_retries=2,
        )

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


def invoke_with_retry(llm: BaseChatModel, messages: list) -> str:
    """
    Call llm.invoke() with automatic retry + backoff on any transient error
    (rate limits, timeouts, network errors). Returns the response content string.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Add a small delay between calls to avoid hitting rate limits
            if attempt > 1:
                delay = RETRY_BASE_DELAY * attempt
                print(f"   ⏳ Retry {attempt}/{MAX_RETRIES}. Waiting {delay}s...")
                time.sleep(delay)
            response = llm.invoke(messages)
            # Brief pause after success to respect rate limits
            time.sleep(3)
            return response.content.strip()
        except KeyboardInterrupt:
            raise
        except Exception as e:
            err_str = str(e).lower()
            is_transient = any(kw in err_str for kw in [
                "429", "rate", "quota", "too many", "timeout",
                "connection", "ssl", "recv", "reset", "network",
                "resourceexhausted", "unavailable", "500", "502", "503"
            ])
            if is_transient and attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * attempt
                print(f"   ⏳ Transient error (attempt {attempt}/{MAX_RETRIES}): {type(e).__name__}. Waiting {delay}s...")
                time.sleep(delay)
            else:
                raise
    raise RuntimeError(f"Failed after {MAX_RETRIES} retries.")
