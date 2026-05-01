"""
Utility helpers for JobHunter - scoring, keyword overlap, KPI computation.
"""

from __future__ import annotations

from datetime import datetime
from typing import List


DATE_FMT = "%Y-%m-%d"


def compute_skill_overlap(job_skills: List[str], candidate_skills: List[str]) -> float:
    """Calculate percentage overlap between job requirements and candidate skills."""
    if not job_skills:
        return 50.0

    job_set = {s.strip().lower() for s in job_skills}
    cand_set = {s.strip().lower() for s in candidate_skills}

    if not job_set:
        return 50.0

    overlap = job_set & cand_set
    return round((len(overlap) / len(job_set)) * 100, 1)


def apply_seniority_penalty(score: float, job_seniority: str, target_seniority: str) -> float:
    """Drop score when job seniority does not match strategy target."""
    if job_seniority.strip().lower() != target_seniority.strip().lower():
        return round(score * 0.1, 1)
    return score


def _safe_days_between(start_date: str, end_date: str) -> int | None:
    """Return day delta for YYYY-MM-DD dates, otherwise None."""
    try:
        start = datetime.strptime(start_date, DATE_FMT)
        end = datetime.strptime(end_date, DATE_FMT)
        return max((end - start).days, 0)
    except Exception:
        return None


def compute_kpi_metrics(applications: list, usefulness_ratings: list | None = None) -> dict:
    """Compute business KPIs from applications and candidate usefulness ratings."""
    total = len(applications)

    counts = {
        "applied": 0,
        "screening": 0,
        "interviewing": 0,
        "rejected": 0,
        "offer": 0,
    }

    outcome_days: list[int] = []

    for app in applications:
        status = app.get("status", "applied") if isinstance(app, dict) else app.status
        if status in counts:
            counts[status] += 1

        if isinstance(app, dict) and status in ("rejected", "offer"):
            applied_date = app.get("date_applied", "")
            outcome_date = app.get("date_outcome", "") or app.get("date_last_updated", "")
            days = _safe_days_between(applied_date, outcome_date)
            if days is not None:
                outcome_days.append(days)

    interview_eligible = counts["interviewing"] + counts["offer"]
    interview_rate = (interview_eligible / total * 100) if total > 0 else 0.0
    offer_rate = (counts["offer"] / max(interview_eligible, 1) * 100) if interview_eligible > 0 else 0.0

    avg_outcome_days = round(sum(outcome_days) / len(outcome_days), 1) if outcome_days else None

    ratings = usefulness_ratings or []
    usefulness_avg = round(sum(ratings) / len(ratings), 2) if ratings else None

    return {
        "total_applications": total,
        **counts,
        "interview_conversion_rate": round(interview_rate, 1),
        "offer_rate": round(offer_rate, 1),
        "avg_days_to_outcome": avg_outcome_days,
        "pattern_usefulness_avg": usefulness_avg,
        "pattern_usefulness_count": len(ratings),
    }


def normalize_skills(skills_str: str) -> List[str]:
    """Split a comma-separated skills string into a cleaned list."""
    if not skills_str:
        return []
    return [s.strip() for s in skills_str.split(",") if s.strip()]
