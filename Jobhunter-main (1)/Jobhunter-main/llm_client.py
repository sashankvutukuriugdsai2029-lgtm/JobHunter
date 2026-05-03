import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

def get_llm_client() -> OpenAI:
    """
    Returns an OpenAI-compatible client pointed 
    at OpenRouter API.
    All LLM nodes import this function.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv(
        "OPENROUTER_BASE_URL", 
        "https://openrouter.ai/api/v1"
    )
    
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not found in .env file. "
            "Please add it to jobhunter/.env"
        )
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )
    return client

def get_model_name() -> str:
    """Returns the model name from .env"""
    return os.getenv(
        "OPENROUTER_MODEL", 
        "google/gemma-3-27b-it:free"
    )

def call_llm(prompt: str, 
             system: str = "You are a helpful assistant.",
             max_tokens: int = 500) -> str:
    client = get_llm_client()
    model = get_model_name()
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens
        )
        message = response.choices[0].message
        
        # Try content first (normal models)
        if message.content and message.content.strip():
            return message.content.strip()
        
        # Reasoning models put answer in reasoning field
        # Extract just the final answer from reasoning text
        if hasattr(message, 'reasoning') and message.reasoning:
            reasoning_text = message.reasoning
            # The reasoning model thinks out loud then concludes
            # Take the last sentence which is usually the answer
            lines = [l.strip() for l in reasoning_text.split('\n') 
                     if l.strip()]
            # Look for a line that looks like keywords (has commas)
            for line in reversed(lines):
                if ',' in line and len(line) < 200:
                    return line.strip()
            # fallback: return last non-empty line
            if lines:
                return lines[-1]
        
        return ""
    except Exception as e:
        print(f"[LLM ERROR] {type(e).__name__}: {e}")
        return ""

if __name__ == "__main__":
    # Test the connection
    print("Testing OpenRouter connection...")
    response = call_llm(
        prompt="Say hello in exactly 5 words.",
        system="You are a helpful assistant."
    )
    print(f"LLM Response: {response}")
    if response:
        print("OpenRouter connection working correctly!")
    else:
        print("ERROR: No response received. Check your API key.")
