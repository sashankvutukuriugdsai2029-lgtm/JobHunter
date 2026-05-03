import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import JobHunterState, CandidateProfile

def calculate_match_score(job: dict, profile: CandidateProfile) -> int:
    """
    Calculates a match score (0-100) for a job against a candidate profile.
    Based on skills, target roles, experience level, and remote preference.
    """
    score = 0.0

    # SKILLS CHECK (max 40 points)
    skills = profile.skills
    if skills:
        points_per_skill = 40.0 / len(skills)
        desc = str(job.get("description", "")).lower()
        skills_desc = str(job.get("skills_desc", "")).lower()
        
        for skill in skills:
            skill_lower = skill.lower()
            if skill_lower in desc or skill_lower in skills_desc:
                score += points_per_skill
                
    score = min(score, 40.0)

    # ROLE MATCH CHECK (max 30 points)
    target_roles = profile.target_roles
    title = str(job.get("title", "")).lower()
    role_matched = False
    
    for target in target_roles:
        words = target.lower().split()
        for word in words:
            if word in title:
                role_matched = True
                break
        if role_matched:
            break
            
    if role_matched:
        score += 30.0

    # EXPERIENCE LEVEL CHECK (max 20 points)
    exp_years = profile.experience_years
    if exp_years <= 1:
        expected_levels = ["Entry level", "Internship"]
    elif exp_years <= 4:
        expected_levels = ["Associate", "Mid-Senior level"]
    else:
        expected_levels = ["Mid-Senior level", "Director"]
        
    job_level = job.get("formatted_experience_level", "")
    if job_level in expected_levels:
        score += 20.0

    # REMOTE BONUS (max 10 points)
    if job.get("remote_allowed") is True:
        score += 10.0

    return int(min(score, 100))

def matcher(state: JobHunterState) -> dict:
    """
    Third node in the LangGraph workflow.
    Calculates a match_score for each job based on candidate profile.
    """
    jobs = list(state.recommended_jobs)
    
    # STEP 1: Check if recommended_jobs is empty
    if not jobs:
        return {"recommended_jobs": jobs}
        
    print(f"[matcher] Scoring {len(jobs)} jobs...")
    
    profile = state.candidate_profile
    
    # STEP 2: Check if candidate_profile is None
    if profile is None:
        print("[matcher] WARNING: candidate_profile is None. Assigning default score of 50.")
        for job in jobs:
            job["match_score"] = 50
        return {"recommended_jobs": jobs}
        
    print(f"[matcher] Profile: {profile.name}")
    
    total_score = 0
    # STEP 3: For each job in recommended_jobs calculate score
    for job in jobs:
        score = calculate_match_score(job, profile)
        job["match_score"] = score
        total_score += score
        
    avg_score = total_score / len(jobs) if jobs else 0
    print(f"[matcher] Avg score: {avg_score:.1f}")
    
    # STEP 4: Return updated recommended_jobs
    return {"recommended_jobs": jobs}

if __name__ == "__main__":
    from state import create_fresh_state, CandidateProfile

    # Test 1: With candidate profile
    state = create_fresh_state()
    
    # Add fake jobs (simulating job_fetcher output)
    state.recommended_jobs = [
        {
            "job_id": "001",
            "company_name": "TechCorp",
            "title": "Software Engineer",
            "description": "Python and React developer needed",
            "skills_desc": "Python, React, SQL",
            "formatted_experience_level": "Entry level",
            "remote_allowed": True,
            "location": "New York",
            "normalized_salary": 90000,
            "application_url": "",
            "formatted_work_type": "Full-time"
        },
        {
            "job_id": "002",
            "company_name": "StartupXYZ",
            "title": "Backend Developer",
            "description": "Java and Node.js experience required",
            "skills_desc": "Java, Node.js",
            "formatted_experience_level": "Mid-Senior level",
            "remote_allowed": False,
            "location": "San Francisco",
            "normalized_salary": 120000,
            "application_url": "",
            "formatted_work_type": "Full-time"
        }
    ]
    
    # Add candidate profile
    state.candidate_profile = CandidateProfile(
        name="Arjun",
        skills=["Python", "React", "SQL"],
        target_roles=["Software Engineer", "Backend Developer"],
        experience_years=0
    )
    
    result = matcher(state)
    print(f"\nTest 1 Results:")
    for job in result["recommended_jobs"]:
        print(f"  {job['title']} at {job['company_name']}: score = {job['match_score']}")

    # Test 2: No profile (should give score 50 to all)
    state2 = create_fresh_state()
    state2.recommended_jobs = [
        {
            "job_id": "003",
            "company_name": "AnyCompany",
            "title": "Data Analyst",
            "description": "SQL and Python needed",
            "skills_desc": "",
            "formatted_experience_level": "Entry level",
            "remote_allowed": False,
            "location": "Remote",
            "normalized_salary": 70000,
            "application_url": "",
            "formatted_work_type": "Full-time"
        }
    ]
    result2 = matcher(state2)
    print(f"\nTest 2 - No profile score: {result2['recommended_jobs'][0]['match_score']}")
    print("Should be 50")

    print("\nmatcher working correctly!")
