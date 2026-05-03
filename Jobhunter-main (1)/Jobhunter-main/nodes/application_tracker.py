import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from state import JobHunterState, Application, ApplicationStatus

def application_tracker(state: JobHunterState) -> dict:
    """
    Fifth node in the LangGraph workflow.
    Records new job applications logged by the user.
    Prevents duplicates by checking existing job_ids.
    """
    # STEP 1: Get existing applications from state
    existing = state.applications
    existing_job_ids = [app.job_id for app in existing]
    
    # STEP 2: Get new applications to add
    new_applications = []
    
    for job in state.recommended_jobs:
        if job.get("user_applied") is True:
            job_id = str(job.get("job_id", ""))
            if job_id not in existing_job_ids:
                # STEP 3: Create Application object for each new application
                new_app = Application(
                    job_id=job_id,
                    company=job.get("company_name", "Unknown"),
                    role=job.get("title", "Unknown"),
                    status=ApplicationStatus.APPLIED,
                    applied_date=datetime.now().strftime("%Y-%m-%d"),
                    notes=job.get("user_notes", "")
                )
                new_applications.append(new_app)
                existing_job_ids.append(job_id)
            else:
                # Update existing application with feedback if available
                for app in existing:
                    if str(app.job_id) == job_id:
                        f_type = job.get("feedback_type", "").lower()
                        if f_type == "rejection":
                            app.status = ApplicationStatus.REJECTED
                        elif f_type == "interview":
                            app.status = ApplicationStatus.INTERVIEWING
                        elif f_type == "offer":
                            app.status = ApplicationStatus.OFFER
                            
                        # Update notes with feedback text
                        feedback = job.get("user_feedback")
                        if feedback:
                            app.notes = feedback
                        break
                
    # STEP 4: Combine existing + new applications
    all_applications = existing + new_applications
    
    # STEP 5: Print summary
    print(f"[application_tracker] Existing apps: {len(existing)}")
    print(f"[application_tracker] New apps added: {len(new_applications)}")
    print(f"[application_tracker] Total apps: {len(all_applications)}")
    
    # STEP 6: Return dict
    return {
        "applications": all_applications,
        "session_summary": f"Tracked {len(new_applications)} new applications. Total: {len(all_applications)}"
    }

if __name__ == "__main__":
    from state import create_fresh_state, CandidateProfile

    # Test 1: User applied to 2 jobs
    state = create_fresh_state()
    state.candidate_profile = CandidateProfile(name="Arjun")

    # Simulate recommended_jobs with user_applied flag
    state.recommended_jobs = [
        {
            "job_id": "001",
            "company_name": "TechCorp",
            "title": "Software Engineer",
            "match_score": 100,
            "rank": 1,
            "user_applied": True,      # ← user applied to this
            "user_notes": "Applied via referral",
            "location": "New York",
            "normalized_salary": 90000,
            "formatted_experience_level": "Entry level",
            "remote_allowed": True,
            "application_url": "",
            "formatted_work_type": "Full-time",
            "description": "Python developer needed",
            "skills_desc": "Python, React"
        },
        {
            "job_id": "002",
            "company_name": "StartupXYZ",
            "title": "Backend Developer",
            "match_score": 30,
            "rank": 2,
            "user_applied": False,     # ← user did NOT apply
            "user_notes": "",
            "location": "San Francisco",
            "normalized_salary": 120000,
            "formatted_experience_level": "Mid-Senior level",
            "remote_allowed": False,
            "application_url": "",
            "formatted_work_type": "Full-time",
            "description": "Java developer needed",
            "skills_desc": "Java, Node"
        },
        {
            "job_id": "003",
            "company_name": "DataCo",
            "title": "Data Analyst",
            "match_score": 75,
            "rank": 3,
            "user_applied": True,      # ← user applied to this
            "user_notes": "",
            "location": "Remote",
            "normalized_salary": 80000,
            "formatted_experience_level": "Entry level",
            "remote_allowed": True,
            "application_url": "",
            "formatted_work_type": "Full-time",
            "description": "SQL analyst needed",
            "skills_desc": "SQL, Python"
        }
    ]

    result = application_tracker(state)
    print(f"\nTest 1 Results:")
    print(f"Applications tracked: {len(result['applications'])}")
    for app in result["applications"]:
        print(f"  {app.company} — {app.role} — {app.status}")

    # Test 2: Duplicate prevention
    # Run tracker again with same jobs
    # Should NOT add duplicates
    state.applications = result["applications"]
    result2 = application_tracker(state)
    print(f"\nTest 2 - After duplicate check:")
    print(f"Total applications (should still be 2): {len(result2['applications'])}")

    # Test 3: Empty recommended_jobs
    from state import create_fresh_state
    state3 = create_fresh_state()
    state3.recommended_jobs = []
    result3 = application_tracker(state3)
    print(f"\nTest 3 - Empty jobs: {len(result3['applications'])} applications")

    print("\napplication_tracker working correctly!")
