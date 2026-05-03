import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from state import JobHunterState

def job_fetcher(state: JobHunterState) -> dict:
    """
    Second node in the LangGraph workflow.
    Reads jobs.csv and filters them based on the candidate's current search strategy.
    Returns matching jobs as a list of dictionaries in recommended_jobs.
    """
    if state.current_strategy is None:
        print("[job_fetcher] No current strategy found. Filtering skipped.")
        return {
            "recommended_jobs": [],
            "session_summary": "No current search strategy set. Cannot fetch jobs."
        }

    seniority = state.current_strategy.seniority_level
    locations = state.current_strategy.locations
    role_types = state.current_strategy.role_types
    avoid_keywords = state.current_strategy.avoid_keywords

    print(f"[job_fetcher] Seniority: {seniority}")
    print(f"[job_fetcher] Locations: {locations}")

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(BASE_DIR, "data", "jobs.csv")

    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"[job_fetcher] Error loading jobs data: {e}")
        return {
            "recommended_jobs": [],
            "session_summary": "Error loading jobs database."
        }

    # STEP 3: Map seniority_level to experience levels
    experience_map = {
        "junior": ["Entry level", "Associate", "Internship"],
        "mid": ["Mid-Senior level", "Associate"],
        "senior": ["Mid-Senior level", "Director"]
    }
    target_experience = experience_map.get(seniority.lower(), experience_map["junior"])

    # STEP 4: Filter jobs by experience level
    df = df[df["formatted_experience_level"].isin(target_experience)]

    # STEP 5: Filter by location (if locations list is not empty)
    if locations:  # only filter if locations list is NOT empty
        loc_pattern = "|".join([str(loc).lower() for loc in locations])
        contain_loc = df["location"].str.lower().str.contains(
            loc_pattern, na=False)
        is_remote = df["remote_allowed"].astype(str).str.lower().isin(
            ["true", "1", "1.0"])
        df = df[contain_loc | is_remote]
        print(f"[job_fetcher] After location filter: {len(df)} jobs")
    else:
        print(f"[job_fetcher] No location filter — showing all locations")

    # STEP 6: Filter by role_types (if role_types list is not empty)
    if role_types:
        role_pattern = "|".join([str(role).lower() for role in role_types])
        df = df[df["title"].str.lower().str.contains(role_pattern, na=False)]

    # STEP 7: Filter by avoid_keywords (if list is not empty)
    if avoid_keywords:
        avoid_pattern = "|".join([str(kw).lower() for kw in avoid_keywords])
        mask1 = df["title"].str.lower().str.contains(avoid_pattern, na=False)
        mask2 = df["description"].str.lower().str.contains(avoid_pattern, na=False)
        df = df[~(mask1 | mask2)]

    print(f"[job_fetcher] Jobs found after filtering: {len(df)}")

    # STEP 8: Convert remaining jobs to list of dicts
    jobs_list = df.to_dict(orient="records")

    # PRESERVE user interaction fields from existing state
    existing_jobs = {str(j.get("job_id", "")): j for j in state.recommended_jobs}
    for j in jobs_list:
        j_id = str(j.get("job_id", ""))
        if j_id in existing_jobs:
            if existing_jobs[j_id].get("user_applied"):
                j["user_applied"] = existing_jobs[j_id].get("user_applied")
            if existing_jobs[j_id].get("user_feedback"):
                j["user_feedback"] = existing_jobs[j_id].get("user_feedback")
            if existing_jobs[j_id].get("feedback_type"):
                j["feedback_type"] = existing_jobs[j_id].get("feedback_type")

    # STEP 9: Return dict with recommended_jobs
    return {
        "recommended_jobs": jobs_list,
        "session_summary": f"Found {len(jobs_list)} matching jobs"
    }

if __name__ == "__main__":
    from state import create_fresh_state, SearchStrategy

    # Test 1: Default strategy (junior, Bangalore/Remote)
    state = create_fresh_state()
    result = job_fetcher(state)
    print(f"Test 1 - Jobs found: {len(result['recommended_jobs'])}")
    if result['recommended_jobs']:
        print(f"Sample job: {result['recommended_jobs'][0]['title']} at {result['recommended_jobs'][0]['company_name']}")

    # Test 2: Senior level strategy
    state2 = create_fresh_state()
    state2.current_strategy.seniority_level = "senior"
    result2 = job_fetcher(state2)
    print(f"Test 2 - Senior jobs found: {len(result2['recommended_jobs'])}")

    # Test 3: No strategy (edge case)
    state3 = create_fresh_state()
    state3.current_strategy = None
    result3 = job_fetcher(state3)
    print(f"Test 3 - No strategy: {len(result3['recommended_jobs'])} jobs")

    print("\njob_fetcher working correctly!")
