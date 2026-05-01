"""
job_fetcher — Reads jobs.csv and filters by current strategy's target seniority.
"""

from __future__ import annotations

import os

import pandas as pd

from src.utils import normalize_skills


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def job_fetcher(state: dict) -> dict:
    """Fetch jobs from CSV filtered by the current strategy's target seniority."""
    strategy = state.get("current_strategy", {})
    target_seniority = strategy.get("target_seniority", "Senior")
    focus_areas = [s.lower() for s in strategy.get("focus_areas", [])]

    csv_path = os.path.join(DATA_DIR, "jobs.csv")
    df = pd.read_csv(csv_path)

    # Primary filter: match seniority
    # The new CSV uses 'formatted_experience_level' instead of 'seniority'
    if "formatted_experience_level" in df.columns:
        seniority_col = "formatted_experience_level"
    else:
        seniority_col = "seniority"
        
    filtered = df[df[seniority_col].str.strip().str.lower() == target_seniority.strip().lower()]

    # If no matches (shouldn't happen with our dataset), fall back to all
    if filtered.empty:
        filtered = df

    from src.models import CompanySignals
    import random
    
    def _mock_signals(company: str) -> dict:
        """Deterministic mock for company signals based on name length."""
        seed = len(company)
        stages = ["Public", "Series C", "Series B", "Series A", "Bootstrapped"]
        stage = stages[seed % len(stages)]
        
        fundings = ["$1B+", "$150M", "$45M", "$12M", "N/A"]
        funding = fundings[seed % len(fundings)]
        
        growths = ["↑ 32% YoY", "↑ 12% YoY", "↑ 5% YoY", "↓ 2% YoY", "↑ 50% YoY"]
        growth = growths[seed % len(growths)]
        
        rating = 3.5 + (seed % 15) / 10.0  # 3.5 to 4.9
        
        headlines = [
            f"{company} announces major product expansion",
            f"{company} ranked top workplace 2025",
            f"New funding round accelerates {company} growth",
            f"{company} acquiring competitor",
            f"Record Q3 revenue for {company}",
        ]
        headline = headlines[seed % len(headlines)]
        
        return CompanySignals(
            funding_stage=stage,
            total_funding=funding,
            headcount_growth=growth,
            recent_news_headline=headline,
            glassdoor_rating=round(rating, 1)
        ).model_dump()

    jobs = []
    for _, row in filtered.iterrows():
        # Handle different column names between old and new CSV formats
        company_name = row.get("company_name", row.get("company", "Unknown"))
        skills_raw = row.get("skills_desc", row.get("required_skills", ""))
        seniority_val = row.get("formatted_experience_level", row.get("seniority", "Unknown"))
        
        skills = normalize_skills(skills_raw)
        jobs.append({
            "job_id": row["job_id"],
            "company": company_name,
            "title": row["title"],
            "seniority": seniority_val,
            "description": row.get("description", ""),
            "required_skills": skills,
            "fit_score": 0.0,  # Will be computed by matcher
            "company_signals": _mock_signals(company_name)
        })

    return {"matched_jobs": jobs}

    print('job_fetcher done')
