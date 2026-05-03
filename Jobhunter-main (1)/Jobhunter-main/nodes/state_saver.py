import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from state import JobHunterState

def state_saver(state: JobHunterState) -> dict:
    """
    Ninth and final node in the LangGraph workflow.
    Runs at the end of every session to increment counters,
    update timestamps, and generate a session summary.
    The actual database persistence is handled by LangGraph's checkpointer.
    """
    # STEP 1: Increment sessions_count
    new_count = state.sessions_count + 1

    # STEP 2: Update last_updated
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # STEP 3: Build session summary
    active_patterns = len([p for p in state.rejection_patterns if p.status == "active"])
    total_apps = len(state.applications)
    recommended_count = len(state.recommended_jobs)
    
    seniority = "unknown"
    if state.current_strategy:
        seniority = state.current_strategy.seniority_level
        
    summary_string = (
        f"Session {new_count} complete. "
        f"Jobs recommended: {recommended_count}. "
        f"Applications tracked: {total_apps}. "
        f"Active patterns: {active_patterns}. "
        f"Current seniority: {seniority}."
    )

    # STEP 4: Print what was saved
    print(f"[state_saver] Session {new_count} complete")
    print(f"[state_saver] Applications: {total_apps}")
    print(f"[state_saver] Active patterns: {active_patterns}")
    print(f"[state_saver] Seniority: {seniority}")
    print(f"[state_saver] State ready for checkpointer OK")

    # STEP 5: Return final state fields
    return {
        "sessions_count": new_count,
        "last_updated": last_updated,
        "session_summary": summary_string
    }

if __name__ == "__main__":
    from state import (create_fresh_state, CandidateProfile, 
                       Application, ApplicationStatus, Pattern)
    from datetime import date

    # Test: Full state with applications and patterns
    state = create_fresh_state()
    state.sessions_count = 2
    state.candidate_profile = CandidateProfile(
        name="Arjun",
        skills=["Python", "React"],
        target_roles=["Software Engineer"],
        experience_years=0
    )
    state.applications = [
        Application(
            job_id="001", company="TechCorp",
            role="SWE", status=ApplicationStatus.APPLIED,
            applied_date=str(date.today())
        ),
        Application(
            job_id="002", company="DataCo",
            role="Analyst", status=ApplicationStatus.REJECTED,
            applied_date=str(date.today())
        )
    ]
    state.rejection_patterns = [
        Pattern(
            theme="system design", frequency=4,
            severity="medium", first_detected="2024-01-01",
            status="active",
            suggested_action="Practice system design",
            resources=["Grokking System Design"]
        )
    ]
    state.recommended_jobs = [{"job_id": f"{i}"} 
                               for i in range(10)]
    state.current_strategy.seniority_level = "junior"

    result = state_saver(state)
    print(f"\nResult:")
    print(f"  sessions_count: {result['sessions_count']}")
    print(f"  last_updated: {result['last_updated']}")
    print(f"  session_summary: {result['session_summary']}")
    print("\nstate_saver working correctly!")
