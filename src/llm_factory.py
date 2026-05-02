"""
Centralized LLM Factory for Google Gemini via LangChain.
Uses OPENROUTER_API_KEY from the .env file.
"""

import os

from langchain_openai import ChatOpenAI

def get_llm(temperature: float = 0.2):
    """Return configured ChatOpenAI instance for OpenRouter."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")

    return ChatOpenAI(
        model="inclusionai/ling-2.6-1t:free",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=temperature,
        max_retries=1,
    )
