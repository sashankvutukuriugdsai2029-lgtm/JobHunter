"""
ranker — Sorts scored jobs by fit_score descending, returns top 10.
"""

from __future__ import annotations


def ranker(state: dict) -> dict:
    """Rank jobs by fit score and return the top 10."""
    jobs = state.get("matched_jobs", [])

    # Sort descending by fit_score
    ranked = sorted(jobs, key=lambda j: j.get("fit_score", 0), reverse=True)

    # Return top 50 to give the UI a larger pool to filter from
    top_jobs = ranked[:50]

    return {"matched_jobs": top_jobs}
