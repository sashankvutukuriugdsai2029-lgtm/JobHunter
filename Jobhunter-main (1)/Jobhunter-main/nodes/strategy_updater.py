import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import JobHunterState, Pattern, SearchStrategy, create_default_strategy
from llm_client import call_llm

def strategy_updater(state: JobHunterState) -> dict:
    """
    Eighth node in the LangGraph workflow.
    Adjusts the current search strategy based on detected rejection patterns.
    Uses LLM to suggest targeted preparation resources for active weaknesses.
    """
    # STEP 1: Get active patterns
    rejection_patterns = list(state.rejection_patterns)
    active_patterns = [p for p in rejection_patterns if p.status == "active"]
    
    # Check if ALL patterns are resolved
    all_resolved = len(rejection_patterns) > 0 and len(active_patterns) == 0

    # STEP 2: Get current strategy
    strategy = state.current_strategy
    if strategy is None:
        strategy = create_default_strategy()
        
    if not active_patterns and not all_resolved:
        print("[strategy_updater] No changes needed.")
        return {
            "current_strategy": strategy,
            "rejection_patterns": rejection_patterns,
            "session_summary": "Strategy unchanged (no active or newly resolved patterns)"
        }
        
    old_seniority = strategy.seniority_level.lower()
    new_seniority = old_seniority
    strategy_notes = ""

    # STEP 3: Adjust seniority based on pattern severity
    has_high_severity = any(p.severity == "high" for p in active_patterns)
    
    if has_high_severity:
        if old_seniority == "senior":
            new_seniority = "mid"
        elif old_seniority == "mid":
            new_seniority = "junior"
            
        if old_seniority != new_seniority:
            print(f"[strategy_updater] Seniority lowered: {old_seniority} -> {new_seniority}")
            strategy.seniority_level = new_seniority
            strategy_notes = f"Seniority lowered to {new_seniority} due to high-severity weakness."
            
    elif all_resolved:
        if old_seniority == "junior":
            new_seniority = "mid"
        elif old_seniority == "mid":
            new_seniority = "senior"
            
        if old_seniority != new_seniority:
            print(f"[strategy_updater] Seniority restored: {old_seniority} -> {new_seniority}")
            strategy.seniority_level = new_seniority
            strategy_notes = f"Seniority restored to {new_seniority} because patterns are resolved."

    print(f"[strategy_updater] Active patterns: {len(active_patterns)}")
    print(f"[strategy_updater] Seniority: {old_seniority} -> {new_seniority}")

    resources_added_summary = []

    # STEP 4: For each active pattern, generate prep resources
    for pattern in active_patterns:
        # Avoid regenerating if resources already exist
        if not pattern.resources:
            system = "You are a career coach. Given a job interview weakness theme, suggest exactly 3 specific preparation resources. Return ONLY a comma-separated list of 3 resource names. No explanation. Example output: Grokking System Design book, System Design Primer on GitHub, Practice designing URL shortener"
            user_prompt = f"Suggest 3 prep resources for this interview weakness: {pattern.theme}"
            
            llm_response = call_llm(user_prompt, system, max_tokens=150)
            
            parsed_resources = []
            if llm_response and ',' in llm_response:
                parsed_resources = [r.strip() for r in llm_response.split(',') if r.strip()][:3]
                
            # Fallbacks
            if not parsed_resources or len(parsed_resources) < 1:
                theme_lower = pattern.theme.lower()
                if "system design" in theme_lower:
                    parsed_resources = ["Grokking System Design", "System Design Primer GitHub", "Practice URL shortener design"]
                elif "coding" in theme_lower:
                    parsed_resources = ["LeetCode daily practice", "Cracking the Coding Interview book", "HackerRank challenges"]
                elif "communication" in theme_lower:
                    parsed_resources = ["Mock interview practice", "STAR method for behavioral questions", "Toastmasters communication course"]
                else:
                    parsed_resources = [f"Study {pattern.theme} fundamentals", f"Practice {pattern.theme} problems", f"Read {pattern.theme} documentation"]
                    
            pattern.resources = parsed_resources
            
            # Add resources to strategy.prep_resources (avoid duplicates)
            for res in parsed_resources:
                if res not in strategy.prep_resources:
                    strategy.prep_resources.append(res)
                    resources_added_summary.append(res)
                    
    print(f"[strategy_updater] Resources added: {resources_added_summary}")

    # STEP 5: Update strategy notes
    if not strategy_notes:
        strategy_notes = f"Strategy adjusted based on {len(active_patterns)} active patterns."
    if resources_added_summary:
        strategy_notes += f" {len(resources_added_summary)} prep resources added."
        
    strategy.strategy_notes = strategy_notes

    # STEP 6: Return
    return {
        "current_strategy": strategy,
        "rejection_patterns": rejection_patterns,
        "session_summary": f"Strategy updated: {strategy.strategy_notes}"
    }

if __name__ == "__main__":
    from state import create_fresh_state, Pattern

    # Test 1: High severity pattern — should lower seniority
    state1 = create_fresh_state()
    state1.current_strategy.seniority_level = "mid"
    state1.rejection_patterns = [
        Pattern(
            theme="system design",
            frequency=5,
            severity="high",
            first_detected="2024-01-01",
            status="active",
            suggested_action="Focus on improving: system design",
            resources=[]
        )
    ]
    result1 = strategy_updater(state1)
    print(f"Test 1 - Seniority (should be junior): {result1['current_strategy'].seniority_level}")
    print(f"Test 1 - Prep resources: {result1['current_strategy'].prep_resources}")
    print(f"Test 1 - Pattern resources: {result1['rejection_patterns'][0].resources}")

    print()

    # Test 2: No active patterns — nothing should change
    state2 = create_fresh_state()
    state2.current_strategy.seniority_level = "mid"
    state2.rejection_patterns = []
    result2 = strategy_updater(state2)
    print(f"Test 2 - Seniority unchanged (should be mid): {result2['current_strategy'].seniority_level}")

    print()

    # Test 3: All patterns resolved — seniority should rise
    state3 = create_fresh_state()
    state3.current_strategy.seniority_level = "junior"
    state3.rejection_patterns = [
        Pattern(
            theme="system design",
            frequency=5,
            severity="high",
            first_detected="2024-01-01",
            status="resolved",
            suggested_action="Focus on improving: system design",
            resources=["Grokking System Design"]
        )
    ]
    result3 = strategy_updater(state3)
    print(f"Test 3 - Seniority restored (should be mid): {result3['current_strategy'].seniority_level}")

    print("\nstrategy_updater working correctly!")
