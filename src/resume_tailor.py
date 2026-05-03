"""
Resume Tailoring & Cover Letter Utilities (Tier 3)
Provides on-demand generation without muddying the main graph state.
"""

from __future__ import annotations

import os
from typing import List

RESUME_TAILOR_PROMPT = """
Given this job description and the candidate's resume/profile, suggest 3 specific changes 
to tailor the resume for this role.

Format:
1. [Section to edit] → [What to change] → [Why it helps]

Example:
1. [Skills section] → Add "Distributed Systems" explicitly → JD mentions it 5 times
2. [Experience bullet, Job 2] → Quantify the scale: "handled 10M requests/day" → matches their infra focus
3. [Summary] → Lead with "fintech backend" not "full-stack" → company is pure backend

Be surgical. No generic advice.
"""

COVER_LETTER_PROMPT = """
Write a 3-paragraph cover letter for this candidate applying to this role.

Paragraph 1: Hook — connect their strongest relevant experience to the company's mission.
Paragraph 2: Evidence — two specific achievements that map to the JD requirements.
Paragraph 3: Close — express genuine interest + reference one thing about the company specifically.

Tone: Confident, direct, human. Not corporate. Not sycophantic.
Max 250 words.
"""

def generate_resume_suggestions(job: dict, profile: dict) -> List[str]:
    """Generate 3 specific resume tailoring suggestions."""
    api_key = os.environ.get("GLM_API_KEY", "").strip()
    if not api_key:
        return ["Error: No API key configured."]

    try:
        from src.llm_factory import get_llm
        llm = get_llm(temperature=0.2)

        context = f"""
Candidate: {profile.get('name', 'Candidate')}
Target Role: {profile.get('target_role', '')}
Years Exp: {profile.get('years_experience', 0)}
Skills: {', '.join(profile.get('base_skills', []))}

Job: {job.get('title')} at {job.get('company')}
Description: {job.get('description', '')[:1500]}
"""
        prompt = f"{RESUME_TAILOR_PROMPT}\n\nContext:\n{context}\n\nSuggestions:"
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        
        # Parse into a list of strings
        suggestions = [line.strip() for line in text.split('\n') if line.strip() and line.strip()[0].isdigit()]
        return suggestions if suggestions else [text.strip()]
    except Exception as exc:
        return [f"Error generating suggestions: {exc}"]

def generate_cover_letter(job: dict, profile: dict) -> str:
    """Generate a 3-paragraph cover letter draft."""
    api_key = os.environ.get("GLM_API_KEY", "").strip()
    if not api_key:
        return "Error: No API key configured."

    try:
        from src.llm_factory import get_llm
        llm = get_llm(temperature=0.4)

        context = f"""
Candidate: {profile.get('name', 'Candidate')}
Target Role: {profile.get('target_role', '')}
Years Exp: {profile.get('years_experience', 0)}
Skills: {', '.join(profile.get('base_skills', []))}

Job: {job.get('title')} at {job.get('company')}
Description: {job.get('description', '')[:1500]}
"""
        prompt = f"{COVER_LETTER_PROMPT}\n\nContext:\n{context}\n\nCover Letter:"
        response = llm.invoke(prompt)
        text = response.content if hasattr(response, "content") else str(response)
        return text.strip()
    except Exception as exc:
        return f"Error generating cover letter: {exc}"
