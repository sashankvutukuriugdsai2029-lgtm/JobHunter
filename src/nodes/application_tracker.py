"""
application_tracker — Records new applications logged by the candidate.
Validates status against the 5 allowed enum values.
"""

from __future__ import annotations

from datetime import datetime

from src.models import ApplicationStatus


VALID_STATUSES = {s.value for s in ApplicationStatus}


def application_tracker(state: dict) -> dict:
    """Process and validate new applications added during this session."""
    existing = state.get("applications", [])
    new_apps = state.get("new_applications", [])

    if not new_apps:
        return {}

    validated = []
    for app in new_apps:
        # Enforce valid status
        status = app.get("status", "applied")
        if status not in VALID_STATUSES:
            status = "applied"

        date_applied = app.get("date_applied", datetime.now().strftime("%Y-%m-%d"))
        validated.append({
            "job_id": app.get("job_id", ""),
            "company_name": app.get("company_name", ""),
            "role_title": app.get("role_title", ""),
            "status": status,
            "date_applied": date_applied,
            "date_last_updated": app.get("date_last_updated", date_applied),
            "date_outcome": app.get("date_outcome", ""),
        })

    # Track positive events for strategy cooldown
    strategy = state.get("current_strategy", {})
    positive_count = strategy.get("positive_events_since_last_change", 0)
    for app in validated:
        if app["status"] in ("screening", "interviewing", "offer"):
            positive_count += 1

    updated_strategy = dict(strategy)
    updated_strategy["positive_events_since_last_change"] = positive_count

    return {
        "applications": existing + validated,
        "new_applications": [],  # Clear after processing
        "current_strategy": updated_strategy,
    }
