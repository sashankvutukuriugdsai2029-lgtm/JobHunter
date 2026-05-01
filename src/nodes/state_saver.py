"""
state_saver — Final node that computes KPI metrics before checkpoint.
LangGraph's SqliteSaver handles the actual persistence automatically.
"""

from __future__ import annotations

from src.utils import compute_kpi_metrics


def state_saver(state: dict) -> dict:
    """Compute final KPIs and prepare state for checkpoint."""
    applications = state.get("applications", [])
    usefulness_ratings = state.get("usefulness_ratings", [])
    metrics = compute_kpi_metrics(applications, usefulness_ratings)

    return {
        "kpi_metrics": metrics,
    }
