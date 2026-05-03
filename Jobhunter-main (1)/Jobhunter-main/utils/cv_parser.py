import sys
import os
import json
import PyPDF2

# Ensure llm_client can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm_client import call_llm

def extract_text_from_file(uploaded_file) -> str:
    """Extracts raw text from an uploaded Streamlit file (PDF or TXT)."""
    if uploaded_file.name.lower().endswith(".pdf"):
        text = ""
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"[cv_parser] PDF Extraction error: {e}")
            return ""
    else:
        # Assume it's a text file
        try:
            # Important: return the read pointer to 0 just in case it was read before
            uploaded_file.seek(0) 
            return uploaded_file.read().decode("utf-8")
        except Exception as e:
            print(f"[cv_parser] TXT Extraction error: {e}")
            return ""

def parse_cv_to_profile(cv_text: str) -> dict:
    """Uses the LLM to parse raw CV text into a structured dictionary."""
    if not cv_text or not cv_text.strip():
        return {}

    system_prompt = """You are an expert HR recruiter and JSON parser.
Your task is to extract candidate information from the provided resume text and return it STRICTLY as a valid JSON object. 
Do not include any markdown formatting like ```json, just return the raw JSON object.

The required JSON schema is:
{
  "name": "Full name of the candidate",
  "skills": ["List", "of", "top", "skills", "found"],
  "target_roles": ["Inferred", "or", "stated", "job", "titles"],
  "experience_years": 5,
  "location": "City, State, or Country",
  "education": "Highest degree and university"
}

Rules:
1. If you cannot find a specific field, leave strings empty ("") and lists empty ([]), except experience_years which should be 0 (an integer).
2. Only output the JSON object. Do NOT add any conversational text or explanation.
3. Guess the target_roles based on their previous job titles if not explicitly stated."""

    user_prompt = f"Resume Text:\n\n{cv_text}\n\nExtract the JSON data:"

    response = call_llm(prompt=user_prompt, system=system_prompt, max_tokens=1000)
    
    # Try to parse the JSON
    try:
        # Clean up any potential markdown formatting the LLM might have ignored rules to add
        cleaned_response = response.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
            
        data = json.loads(cleaned_response.strip())
        return data
    except Exception as e:
        print(f"[cv_parser] JSON parsing error: {e}")
        print(f"[cv_parser] Raw LLM Response: {response}")
        return {}
        
if __name__ == "__main__":
    test_cv = "John Doe\nSoftware Engineer located in San Francisco, CA.\nExperience: 4 years working at TechCorp as a Backend Developer using Python, Django, and AWS.\nEducation: B.S. in Computer Science from University of XYZ."
    print("Testing CV Parser...")
    result = parse_cv_to_profile(test_cv)
    print("Parsed Result:")
    print(json.dumps(result, indent=2))
