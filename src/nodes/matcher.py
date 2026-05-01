"""
matcher — Scores each job against the candidate profile.
Now upgraded to a 3-axis MatchScore engine using LLM.
"""

from __future__ import annotations

import json
import os
from typing import List

from pydantic import BaseModel, Field

from src.models import MatchScore
from src.utils import compute_skill_overlap, apply_seniority_penalty

# Pydantic schema for structured output from the LLM
class MatchBreakdown(BaseModel):
    experience_alignment: float = Field(description="0-100: Does YoE match JD requirement?")
    skills_overlap: float = Field(description="0-100: % of required skills candidate has")
    industry_fit: float = Field(description="0-100: How relevant is domain experience")
    missing_skills: List[str] = Field(description="Up to 5 missing skills")
    match_label: str = Field(description="Strong Match, Good Match, Partial Match, Reach")
    match_reason: str = Field(description="One sentence explaining why it's a match (max 20 words)")


def matcher(state: dict) -> dict:
    """Compute fit scores for all matched jobs."""
    jobs = state.get("matched_jobs", [])
    profile = state.get("candidate_profile", {})
    strategy = state.get("current_strategy", {})

    candidate_skills = profile.get("base_skills", [])
    target_seniority = strategy.get("target_seniority", "Senior")
    focus_areas = [s.lower() for s in strategy.get("focus_areas", [])]
    focus_skills = [s.lower() for s in strategy.get("focus_skills", [])]
    all_focus = focus_areas + focus_skills
    
    llm = None
    try:
        from src.llm_factory import get_llm
        base_llm = get_llm(temperature=0)
        llm = base_llm.with_structured_output(MatchBreakdown)
    except Exception:
        llm = None

    scored_jobs = []
    
    # We first do a fast pass to avoid hitting the LLM for 50 jobs
    fast_scored = []
    for job in jobs:
        job_skills = job.get("required_skills", [])
        base_score = compute_skill_overlap(job_skills, candidate_skills)
        focus_overlap = sum(1 for skill in job_skills if skill.lower() in all_focus)
        base_score = min(base_score + (focus_overlap * 10), 100.0)
        base_score = apply_seniority_penalty(base_score, job.get("seniority", ""), target_seniority)
        fast_scored.append((base_score, job))
        
    # Sort and take top 3 for deep LLM evaluation to avoid rate limits / hangs
    fast_scored.sort(key=lambda x: x[0], reverse=True)
    top_candidates = fast_scored[:3]
    
    for base_score, job in top_candidates:
        job_copy = dict(job)
        
        # If LLM is available, get detailed breakdown
        if llm:
            prompt = f"""
            Given this job description and candidate profile, score alignment on three axes.
            
            Candidate: {profile.get('name')}
            Years of Exp: {profile.get('years_experience')}
            Skills: {', '.join(candidate_skills)}
            Focus Areas: {', '.join(all_focus)}
            
            Job: {job.get('title')} at {job.get('company')}
            Seniority: {job.get('seniority')}
            Required Skills: {', '.join(job.get('required_skills', []))}
            Description snippet: {job.get('description', '')[:500]}
            """
            try:
                result = llm.invoke(prompt)
                
                # Combine into overall score (weighted)
                # Boost if focus skills match
                focus_boost = sum(1 for s in all_focus if s in [sk.lower() for sk in job.get('required_skills', [])]) * 5
                
                overall = (result.experience_alignment * 0.3) + (result.skills_overlap * 0.5) + (result.industry_fit * 0.2) + focus_boost
                overall = min(apply_seniority_penalty(overall, job.get("seniority", ""), target_seniority), 100.0)
                
                match_score = MatchScore(
                    overall=round(overall, 1),
                    experience_alignment=round(result.experience_alignment, 1),
                    skills_overlap=round(result.skills_overlap, 1),
                    industry_fit=round(result.industry_fit, 1),
                    missing_skills=result.missing_skills,
                    match_label=result.match_label,
                    match_reason=result.match_reason
                )
                job_copy["fit_score"] = match_score.overall # update legacy for ranker
                job_copy["match_score"] = match_score.model_dump()
            except Exception as e:
                # Fallback on LLM failure
                job_copy["fit_score"] = round(base_score, 1)
        else:
            # Fallback if no LLM
            job_copy["fit_score"] = round(base_score, 1)
            
        scored_jobs.append(job_copy)

    # Add the rest of the jobs with their fast-pass base score
    for base_score, job in fast_scored[3:]:
        job_copy = dict(job)
        job_copy["fit_score"] = round(base_score, 1)
        scored_jobs.append(job_copy)

    return {"matched_jobs": scored_jobs}
