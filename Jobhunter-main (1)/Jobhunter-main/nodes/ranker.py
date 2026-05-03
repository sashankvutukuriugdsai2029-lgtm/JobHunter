import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import JobHunterState

def ranker(state: JobHunterState) -> dict:
    """
    Fourth node in the LangGraph workflow.
    Sorts jobs by match_score descending, returns top 10,
    and assigns a rank to each.
    """
    jobs = list(state.recommended_jobs)
    
    # STEP 2: Handle empty list
    if not jobs:
        print("[ranker] Total jobs to rank: 0")
        return {
            "recommended_jobs": [],
            "session_summary": "No matching jobs found to rank."
        }
        
    print(f"[ranker] Total jobs to rank: {len(jobs)}")
    
    # STEP 3: Sort by match_score descending
    # Sort jobs list by "match_score" key, treating missing as 0
    sorted_jobs = sorted(jobs, key=lambda x: x.get("match_score", 0), reverse=True)
    
    # STEP 4: Take only top 10
    top_jobs = sorted_jobs[:10]
    
    # STEP 5: Add rank field to each job
    for i, job in enumerate(top_jobs):
        job["rank"] = i + 1
        
    print(f"[ranker] Top job: {top_jobs[0]['title']} score={top_jobs[0]['match_score']}")
    print(f"[ranker] Returning top {len(top_jobs)} jobs")
    
    # STEP 6: Return dict
    return {
        "recommended_jobs": top_jobs,
        "session_summary": f"Top {len(top_jobs)} jobs ranked for you"
    }

if __name__ == "__main__":
    from state import create_fresh_state

    # Create state with fake scored jobs
    state = create_fresh_state()
    state.recommended_jobs = [
        {
            "job_id": "001",
            "title": "Software Engineer",
            "company_name": "TechCorp",
            "match_score": 100,
            "location": "New York",
            "normalized_salary": 90000,
            "formatted_experience_level": "Entry level",
            "remote_allowed": True,
            "application_url": ""
        },
        {
            "job_id": "002",
            "title": "Backend Developer",
            "company_name": "StartupXYZ",
            "match_score": 30,
            "location": "San Francisco",
            "normalized_salary": 120000,
            "formatted_experience_level": "Mid-Senior level",
            "remote_allowed": False,
            "application_url": ""
        },
        {
            "job_id": "003",
            "title": "Data Analyst",
            "company_name": "DataCo",
            "match_score": 75,
            "location": "Remote",
            "normalized_salary": 80000,
            "formatted_experience_level": "Entry level",
            "remote_allowed": True,
            "application_url": ""
        },
        {
            "job_id": "004",
            "title": "Full Stack Developer",
            "company_name": "WebAgency",
            "match_score": 85,
            "location": "Austin",
            "normalized_salary": 95000,
            "formatted_experience_level": "Entry level",
            "remote_allowed": False,
            "application_url": ""
        },
        {
            "job_id": "005",
            "title": "ML Engineer",
            "company_name": "AI Labs",
            "match_score": 60,
            "location": "Boston",
            "normalized_salary": 110000,
            "formatted_experience_level": "Entry level",
            "remote_allowed": True,
            "application_url": ""
        }
    ]

    result = ranker(state)
    print(f"\nRanked jobs (top {len(result['recommended_jobs'])}):")
    for job in result["recommended_jobs"]:
        print(f"  Rank {job['rank']}: {job['title']} at {job['company_name']} — score: {job['match_score']}")

    print(f"\nSession summary: {result['session_summary']}")
    print("\nranker working correctly!")
