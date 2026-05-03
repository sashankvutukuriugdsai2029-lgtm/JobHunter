import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from state import JobHunterState, Pattern

def pattern_detector(state: JobHunterState) -> dict:
    """
    Seventh node in the LangGraph workflow.
    Analyzes historical feedback to detect and track recurring weakness themes.
    Requires at least 3 feedback events to trigger.
    """
    # STEP 1: Get all feedback events
    feedback_log = state.feedback_log
    existing_patterns = list(state.rejection_patterns)
    
    if len(feedback_log) < 3:
        print("[pattern_detector] Not enough feedback yet (need 3+).")
        return {
            "rejection_patterns": existing_patterns,
            "session_summary": f"Not enough feedback to detect patterns ({len(feedback_log)}/3)"
        }
        
    print(f"[pattern_detector] Total feedback events: {len(feedback_log)}")

    # STEP 2: Count keyword frequency across ALL feedback events
    keyword_counts = {}
    offer_counts = {}
    rejection_counts = {}
    
    for event in feedback_log:
        f_type = event.feedback_type.lower()
        for keyword in event.keywords_extracted:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
            if f_type == "offer":
                offer_counts[keyword] = offer_counts.get(keyword, 0) + 1
            else:
                rejection_counts[keyword] = rejection_counts.get(keyword, 0) + 1

    print(f"[pattern_detector] Keyword counts: {keyword_counts}")

    # STEP 3: Get existing patterns from state
    pattern_map = {p.theme: p for p in existing_patterns}

    # STEP 4: For each keyword with count >= 3:
    for keyword, count in keyword_counts.items():
        if count >= 3:
            status = "active"
            if offer_counts.get(keyword, 0) > rejection_counts.get(keyword, 0):
                status = "resolved"
                
            severity = "high" if count >= 5 else "medium"
            
            if keyword in pattern_map:
                pattern = pattern_map[keyword]
                pattern.frequency = count
                pattern.severity = severity
                pattern.status = status
            else:
                new_pattern = Pattern(
                    theme=keyword,
                    frequency=count,
                    severity=severity,
                    first_detected=datetime.now().strftime("%Y-%m-%d"),
                    status=status,
                    suggested_action=f"Focus on improving: {keyword}",
                    resources=[]
                )
                existing_patterns.append(new_pattern)
                pattern_map[keyword] = new_pattern
                
    active_patterns = [p for p in existing_patterns if p.status == "active"]
    
    # STEP 5: Print summary
    print(f"[pattern_detector] Patterns detected: {len(existing_patterns)}")
    for p in existing_patterns:
        print(f"  - Theme: {p.theme} | Frequency: {p.frequency} | Status: {p.status}")

    # STEP 6: Return
    return {
        "rejection_patterns": existing_patterns,
        "session_summary": f"Detected {len(active_patterns)} active patterns"
    }

if __name__ == "__main__":
    from state import create_fresh_state, FeedbackEvent

    # Test 1: Not enough feedback (less than 3 events)
    state1 = create_fresh_state()
    state1.feedback_log = [
        FeedbackEvent(
            job_id="001", company="TechCorp",
            feedback_type="rejection",
            feedback_text="system design weak",
            date="2024-01-01",
            keywords_extracted=["system design"]
        ),
        FeedbackEvent(
            job_id="002", company="Zomato",
            feedback_type="rejection",
            feedback_text="system design bad",
            date="2024-01-02",
            keywords_extracted=["system design"]
        )
    ]
    result1 = pattern_detector(state1)
    print(f"Test 1 - Patterns (should be 0): {len(result1['rejection_patterns'])}")

    print()

    # Test 2: Enough feedback, pattern should trigger
    state2 = create_fresh_state()
    state2.feedback_log = [
        FeedbackEvent(
            job_id="001", company="TechCorp",
            feedback_type="rejection",
            feedback_text="system design weak",
            date="2024-01-01",
            keywords_extracted=["system design", "url shortener"]
        ),
        FeedbackEvent(
            job_id="002", company="Zomato",
            feedback_type="rejection",
            feedback_text="system design bad",
            date="2024-01-02",
            keywords_extracted=["system design", "coding"]
        ),
        FeedbackEvent(
            job_id="003", company="Swiggy",
            feedback_type="rejection",
            feedback_text="system design round failed",
            date="2024-01-03",
            keywords_extracted=["system design", "communication"]
        ),
        FeedbackEvent(
            job_id="004", company="CRED",
            feedback_type="rejection",
            feedback_text="struggled with system design",
            date="2024-01-04",
            keywords_extracted=["system design"]
        )
    ]
    result2 = pattern_detector(state2)
    print(f"Test 2 - Patterns detected: {len(result2['rejection_patterns'])}")
    for pattern in result2["rejection_patterns"]:
        print(f"  Theme: {pattern.theme}")
        print(f"  Frequency: {pattern.frequency}")
        print(f"  Severity: {pattern.severity}")
        print(f"  Status: {pattern.status}")
        print(f"  Action: {pattern.suggested_action}")

    print()

    # Test 3: Pattern already exists, update frequency
    state3 = create_fresh_state()
    from state import Pattern
    state3.rejection_patterns = [
        Pattern(
            theme="system design",
            frequency=3,
            severity="medium",
            first_detected="2024-01-01",
            status="active",
            suggested_action="Focus on improving: system design",
            resources=[]
        )
    ]
    state3.feedback_log = [
        FeedbackEvent(
            job_id="001", company="A",
            feedback_type="rejection",
            feedback_text="sd weak",
            date="2024-01-01",
            keywords_extracted=["system design"]
        ),
        FeedbackEvent(
            job_id="002", company="B",
            feedback_type="rejection",
            feedback_text="sd bad",
            date="2024-01-02",
            keywords_extracted=["system design"]
        ),
        FeedbackEvent(
            job_id="003", company="C",
            feedback_type="rejection",
            feedback_text="sd failed",
            date="2024-01-03",
            keywords_extracted=["system design"]
        ),
        FeedbackEvent(
            job_id="004", company="D",
            feedback_type="rejection",
            feedback_text="sd again",
            date="2024-01-04",
            keywords_extracted=["system design"]
        ),
        FeedbackEvent(
            job_id="005", company="E",
            feedback_type="rejection",
            feedback_text="sd once more",
            date="2024-01-05",
            keywords_extracted=["system design"]
        )
    ]
    result3 = pattern_detector(state3)
    print(f"Test 3 - Updated pattern frequency (should be 5, severity high):")
    for pattern in result3["rejection_patterns"]:
        print(f"  Theme: {pattern.theme}, Frequency: {pattern.frequency}, Severity: {pattern.severity}")

    print("\npattern_detector working correctly!")
