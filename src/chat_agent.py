"""
LLM chat helper for direct user-agent communication inside the app.
Uses backend environment key only (GLM_API_KEY).
"""

from __future__ import annotations

import os
from typing import Any


def _build_context(profile: dict[str, Any], state: dict[str, Any]) -> str:
    strategy = state.get("current_strategy", {})
    kpi = state.get("kpi_metrics", {})
    patterns = state.get("rejection_patterns", [])
    apps = state.get("applications", [])

    return (
        f"Candidate name: {profile.get('name', 'Unknown')}\n"
        f"Target role: {profile.get('target_role', 'Unknown')}\n"
        f"Years experience: {profile.get('years_experience', 0)}\n"
        f"Base skills: {', '.join(profile.get('base_skills', []))}\n"
        f"Current target seniority: {strategy.get('target_seniority', 'Unknown')}\n"
        f"Focus areas: {', '.join(strategy.get('focus_areas', []))}\n"
        f"Prep recommendations: {', '.join(strategy.get('prep_recommendations', []))}\n"
        f"Tracked applications: {len(apps)}\n"
        f"Interview conversion rate: {kpi.get('interview_conversion_rate', 0)}%\n"
        f"Offer rate: {kpi.get('offer_rate', 0)}%\n"
        f"Detected patterns: {', '.join(p.get('theme', '') for p in patterns) if patterns else 'None'}"
    )


def ask_agent(message: str, profile: dict[str, Any], state: dict[str, Any]) -> str:
    """Generate assistant reply for in-app chat."""
    api_key = os.environ.get("GLM_API_KEY", "").strip()
    if not api_key:
        return (
            "Backend LLM key is not configured. Add GLM_API_KEY to .env on the server, "
            "restart the app, and chat will work automatically."
        )

    try:
        from src.llm_factory import get_llm
        llm = get_llm(temperature=0.3)

        system_prompt = (
            "You are JobHunter Copilot, a practical career assistant. "
            "Give specific, concise, actionable advice based on the candidate context. "
            "If asked for plans, provide clear next steps."
        )
        context = _build_context(profile, state)
        prompt = (
            f"{system_prompt}\n\n"
            f"Candidate context:\n{context}\n\n"
            f"User question:\n{message}\n\n"
            "Answer:"
        )
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        return (text or "").strip() or "I could not generate a response. Please try again."
    except Exception as exc:
        return f"Agent chat error: {exc}"
