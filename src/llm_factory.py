"""
Centralized LLM Factory for GLM-4.5-Flash via LangChain.
Uses GLM_API_KEY and GLM_BASE_URL from the .env file.
"""

import os

from langchain_openai import ChatOpenAI


def get_llm(temperature: float = 0.2):
    """Return configured ChatOpenAI instance for GLM-4.5-Flash."""
    api_key = os.environ.get("GLM_API_KEY", "")
    base_url = os.environ.get("GLM_BASE_URL", "https://api.z.ai/api/coding/paas/v4")

    return ChatOpenAI(
        model="GLM-4.5-Flash",
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
        max_retries=1,
    )
