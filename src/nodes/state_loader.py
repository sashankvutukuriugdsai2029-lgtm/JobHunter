"""
state_loader - Loads candidate profile, application history, and strategy context.
On cold start, it honors explicitly provided profile and strategy from the UI.
"""

from __future__ import annotations


def _infer_default_strategy_from_profile(profile: dict) -> dict:
    years = int(profile.get("years_experience", 0) or 0)
    if years <= 2:
        seniority = "Junior"
    elif years <= 5:
        seniority = "Mid-Level"
    else:
        seniority = "Senior"

    return {
        "target_seniority": seniority,
        "focus_areas": list(profile.get("base_skills", [])[:3]),
        "prep_recommendations": [],
        "locked_changes": [],
        "positive_events_since_last_change": 0,
    }


def state_loader(state: dict) -> dict:
    """Load or initialize candidate state."""
    session_count = state.get("session_count", state.get("sessions_count", 0))
    candidate_profile = state.get("candidate_profile") or {}
    current_strategy = state.get("current_strategy") or {}

    if session_count == 0:
        strategy = current_strategy or _infer_default_strategy_from_profile(candidate_profile)
        return {
            "candidate_profile": candidate_profile,
            "current_strategy": strategy,
            "applications": state.get("applications", []),
            "feedback_log": state.get("feedback_log", []),
            "rejection_patterns": state.get("rejection_patterns", []),
            "session_count": 1,
            "sessions_count": 1,
            "matched_jobs": [],
            "kpi_metrics": state.get("kpi_metrics", {}),
            "strategy_change_log": state.get("strategy_change_log", []),
            "usefulness_ratings": state.get("usefulness_ratings", []),
        }

    return {
        "session_count": session_count + 1,
        "sessions_count": session_count + 1,
        "matched_jobs": [],
    }
