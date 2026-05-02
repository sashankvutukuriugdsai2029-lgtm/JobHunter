import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()
try:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        OPENROUTER_API_KEY=os.environ["OPENROUTER_API_KEY"],
        max_retries=1
    )
    res = llm.invoke("Hi")
    print("API KEY WORKS:", res.content)
except Exception as e:
    print("API KEY FAILED:", str(e))
