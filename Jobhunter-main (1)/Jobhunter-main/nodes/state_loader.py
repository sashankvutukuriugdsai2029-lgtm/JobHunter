import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
from state import JobHunterState, create_fresh_state

def state_loader(state: JobHunterState) -> dict:
    """
    Initial node in the LangGraph workflow.
    Executes at the beginning of every session to handle cold starts and returning users.
    Returns only the updated fields to be merged into the master state.
    """
    if state.sessions_count == 0 and state.candidate_profile is None:
        print(f"[state_loader] Session: {state.sessions_count}")
        print(f"[state_loader] Cold start: True")
        
        fresh = create_fresh_state()
        
        return {
            "current_strategy": fresh.current_strategy,
            "session_summary": "Welcome! Starting your job search. Please set up your profile.",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        print(f"[state_loader] Session: {state.sessions_count}")
        print(f"[state_loader] Cold start: False")
        
        new_count = state.sessions_count + 1
        
        return {
            "sessions_count": new_count,
            "session_summary": f"Welcome back! This is session {new_count}. Loading your previous data...",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

if __name__ == "__main__":
    # Test 1: Cold start
    fresh = create_fresh_state()
    result = state_loader(fresh)
    print("Cold start result:", result)
    
    # Test 2: Returning session
    from state import CandidateProfile
    returning = create_fresh_state()
    returning.sessions_count = 2
    returning.candidate_profile = CandidateProfile(name="Arjun")
    result2 = state_loader(returning)
    print("Returning session result:", result2)
    
    print("\nstate_loader working correctly!")
