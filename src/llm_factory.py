"""
Centralized LLM Factory for Google Gemini via LangChain.
Uses GOOGLE_API_KEY from the .env file.
"""

import os

from langchain_google_genai import ChatGoogleGenerativeAI


def get_llm(temperature: float = 0.2):
    """Return configured ChatGoogleGenerativeAI instance for Gemini."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")

    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=temperature,
    )
