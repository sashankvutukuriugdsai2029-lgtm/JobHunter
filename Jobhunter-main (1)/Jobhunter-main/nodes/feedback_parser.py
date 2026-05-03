import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from state import JobHunterState, FeedbackEvent
from llm_client import call_llm

def feedback_parser(state: JobHunterState) -> dict:
    """
    Sixth node in the LangGraph workflow.
    Looks at state.recommended_jobs for any job where user has entered feedback.
    Uses LLM to extract keywords from the feedback text.
    Creates FeedbackEvent objects and adds them to feedback_log.
    """
    existing_feedback = state.feedback_log
    existing_job_ids = [event.job_id for event in existing_feedback]
    
    new_events = []
    
    # STEP 1: Find jobs with user feedback
    jobs_with_feedback = [job for job in state.recommended_jobs 
                          if job.get("user_feedback") and str(job["user_feedback"]).strip() != ""]
                          
    print(f"[feedback_parser] Jobs with feedback: {len(jobs_with_feedback)}")

    # STEP 2: For each job with feedback:
    for job in jobs_with_feedback:
        job_id = str(job.get("job_id", ""))
        
        # STEP 4: Avoid duplicates
        if job_id in existing_job_ids:
            continue
            
        feedback_text = job["user_feedback"]
        feedback_type = job.get("feedback_type", "rejection")
        
        system = """You are a keyword extractor for job interview feedback.
Your job is to identify which of these specific themes appear in 
the feedback:
system design, coding, communication, leadership, sql, python, 
java, react, algorithms, data structures, problem solving, teamwork,
experience, technical skills, behavioral, culture fit, domain knowledge,
url shortener, scalability, architecture, design patterns, databases,
networking, cloud, devops, testing, debugging, performance, security

Rules:
- Look at the feedback and find which themes from the list above are mentioned
- Return ONLY the matching themes as a comma-separated list
- Use the exact theme names from the list above
- Return maximum 5 themes
- If none match, return: none
- Do not add any explanation or extra words"""

        user_prompt = f"""Feedback: "{feedback_text}"

Which themes from the list appear in this feedback? 
Return only comma-separated theme names:"""

        llm_response = call_llm(user_prompt, system, max_tokens=150)

        VALID_KEYWORDS = [
            "system design", "coding", "communication", "leadership",
            "sql", "python", "java", "react", "algorithms", 
            "data structures", "problem solving", "teamwork",
            "experience", "technical skills", "behavioral", 
            "culture fit", "domain knowledge", "url shortener",
            "scalability", "architecture", "design patterns",
            "databases", "networking", "cloud", "devops",
            "testing", "debugging", "performance", "security",
            "sql skills", "job offer"
        ]

        # Extract only valid keywords from the LLM response
        response_lower = llm_response.lower()
        keywords = []
        for kw in VALID_KEYWORDS:
            if kw in response_lower:
                keywords.append(kw)
                if len(keywords) >= 5:
                    break

        # If LLM gave nothing useful, fall back to searching feedback directly
        if not keywords:
            feedback_lower = feedback_text.lower()
            keywords = [kw for kw in VALID_KEYWORDS if kw in feedback_lower][:5]
            
        print(f"[feedback_parser] Extracted keywords: {keywords}")
        
        # STEP 3: Create FeedbackEvent object
        event = FeedbackEvent(
            job_id=job_id,
            company=job.get("company_name", "Unknown"),
            feedback_type=feedback_type,
            feedback_text=feedback_text,
            date=datetime.now().strftime("%Y-%m-%d"),
            keywords_extracted=keywords
        )
        
        new_events.append(event)
        existing_job_ids.append(job_id)
        
    updated_feedback_log = existing_feedback + new_events
    print(f"[feedback_parser] Total feedback events: {len(updated_feedback_log)}")
    
    # STEP 5: Return updated feedback_log
    return {
        "feedback_log": updated_feedback_log,
        "session_summary": f"Parsed {len(new_events)} feedback entries"
    }

if __name__ == "__main__":
    from state import create_fresh_state

    state = create_fresh_state()

    # Simulate jobs where user entered feedback
    state.recommended_jobs = [
        {
            "job_id": "001",
            "company_name": "TechCorp",
            "title": "Software Engineer",
            "user_applied": True,
            "user_feedback": "Interviewer said my system design was very weak. Could not explain how to design a URL shortener.",
            "feedback_type": "rejection",
            "match_score": 100,
            "location": "New York",
            "normalized_salary": 90000,
            "formatted_experience_level": "Entry level",
            "remote_allowed": True,
            "application_url": "",
            "formatted_work_type": "Full-time",
            "description": "Python developer",
            "skills_desc": "Python, React"
        },
        {
            "job_id": "002",
            "company_name": "DataCo",
            "title": "Data Analyst",
            "user_applied": True,
            "user_feedback": "Great interview! They loved my SQL skills. Offer expected soon.",
            "feedback_type": "offer",
            "match_score": 75,
            "location": "Remote",
            "normalized_salary": 80000,
            "formatted_experience_level": "Entry level",
            "remote_allowed": True,
            "application_url": "",
            "formatted_work_type": "Full-time",
            "description": "SQL analyst",
            "skills_desc": "SQL, Python"
        },
        {
            "job_id": "003",
            "company_name": "StartupXYZ",
            "title": "Backend Developer",
            "user_applied": False,
            "user_feedback": "",  # no feedback — skip this
            "feedback_type": "rejection",
            "match_score": 30,
            "location": "SF",
            "normalized_salary": 120000,
            "formatted_experience_level": "Mid-Senior level",
            "remote_allowed": False,
            "application_url": "",
            "formatted_work_type": "Full-time",
            "description": "Java developer",
            "skills_desc": "Java"
        }
    ]

    result = feedback_parser(state)
    print(f"\nFeedback events created: {len(result['feedback_log'])}")
    for event in result["feedback_log"]:
        print(f"  {event.company} — {event.feedback_type}")
        print(f"  Keywords: {event.keywords_extracted}")

    print("\nfeedback_parser working correctly!")
