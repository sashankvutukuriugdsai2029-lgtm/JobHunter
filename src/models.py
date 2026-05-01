"""
Pydantic v2 data models for JobHunter state machine.
All models are strictly typed to prevent the AI from hallucinating invalid states.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Literal

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ApplicationStatus(str, Enum):
    """The 5 mandatory application statuses."""
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEWING = "interviewing"
    REJECTED = "rejected"
    OFFER = "offer"


class Seniority(str, Enum):
    JUNIOR = "Junior"
    MID_LEVEL = "Mid-Level"
    SENIOR = "Senior"


# ---------------------------------------------------------------------------
# Core domain models
# ---------------------------------------------------------------------------

class CandidateProfile(BaseModel):
    """Immutable-ish profile loaded once per candidate."""
    name: str
    base_skills: List[str] = Field(default_factory=list)
    target_role: str = "Software Engineer"
    years_experience: int = 0
    target_salary: str = ""


class SearchStrategy(BaseModel):
    """Dynamic strategy that the agent modifies over sessions."""
    target_seniority: str = Field(
        default="Senior",
        description="e.g., Junior, Mid-Level, Senior",
    )
    focus_areas: List[str] = Field(
        default_factory=list,
        description="Skills to heavily index on",
    )
    prep_recommendations: List[str] = Field(
        default_factory=list,
        description="Resources the user should study based on feedback",
    )
    locked_changes: List[str] = Field(
        default_factory=list,
        description="Strategy changes on cooldown (cannot be reverted for 1 session)",
    )
    positive_events_since_last_change: int = Field(
        default=0,
        description="Count of positive events (screening/interviewing) since last pivot",
    )
    work_type: List[Literal["remote", "hybrid", "onsite"]] = Field(
        default_factory=lambda: ["remote", "hybrid", "onsite"],
        description="Preferred work models",
    )
    min_match_score: float = Field(
        default=60.0,
        description="Only show jobs above this threshold",
    )


class Application(BaseModel):
    """A single job application the candidate has submitted."""
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    company_name: str = ""
    role_title: str = ""
    status: str = Field(
        default=ApplicationStatus.APPLIED.value,
        description="Must be: applied, screening, interviewing, rejected, offer",
    )
    date_applied: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
    )
    date_last_updated: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
    )
    date_outcome: str = Field(
        default="",
        description="Set when status reaches terminal outcome (rejected/offer).",
    )
    cover_letter_draft: Optional[str] = None
    resume_tailoring_notes: Optional[List[str]] = None


class FeedbackEvent(BaseModel):
    """Parsed feedback from a rejection email or manual entry."""
    application_id: str = ""
    raw_email_text: str = ""
    extracted_reason: str = ""
    date_logged: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d"),
    )
    missing_skills_at_application: List[str] = Field(
        default_factory=list,
        description="Missing skills identified at the time of application",
    )
    rejection_themes: List[str] = Field(
        default_factory=list,
        description="Themes explicitly mentioned in rejection feedback",
    )


class Pattern(BaseModel):
    """A recurring theme detected across multiple rejections."""
    theme: str = Field(description="The recurring issue, e.g., 'System Design gap'")
    occurrences: int = Field(description="Number of times this theme appeared")
    proposed_action: str = Field(
        description="What the agent wants to do about it",
    )
    source: Literal["feedback_text", "skill_gap", "both"] = Field(
        default="feedback_text",
        description="Where this pattern came from",
    )


class MatchScore(BaseModel):
    """Detailed 3-axis breakdown of how well a candidate matches a job."""
    overall: float = 0.0
    experience_alignment: float = 0.0
    skills_overlap: float = 0.0
    industry_fit: float = 0.0
    missing_skills: List[str] = Field(default_factory=list)
    match_label: str = "Good Match"
    match_reason: str = ""


class CompanySignals(BaseModel):
    """Tier 4: Company Intelligence signals to enrich job cards."""
    funding_stage: Optional[str] = None
    total_funding: Optional[str] = None
    headcount_growth: Optional[str] = None
    recent_news_headline: Optional[str] = None
    glassdoor_rating: Optional[float] = None


class JobPosting(BaseModel):
    """A job listing from the CSV dataset."""
    job_id: str = ""
    company: str = ""
    title: str = ""
    seniority: str = "Senior"
    description: str = ""
    required_skills: List[str] = Field(default_factory=list)
    fit_score: float = 0.0  # Legacy simple score, kept for backward compat if needed
    match_score: Optional[MatchScore] = None
    company_signals: Optional[CompanySignals] = None


# ---------------------------------------------------------------------------
# LangGraph global state
# ---------------------------------------------------------------------------

class JobHunterStateModel(BaseModel):
    """
    Pydantic representation of graph state for validation and requirement alignment.
    LangGraph runtime still uses the TypedDict state below for mutation semantics.
    """

    candidate_profile: CandidateProfile = Field(default_factory=lambda: CandidateProfile(name=""))
    applications: List[Application] = Field(default_factory=list)
    feedback_log: List[FeedbackEvent] = Field(default_factory=list)
    rejection_patterns: List[Pattern] = Field(default_factory=list)
    current_strategy: SearchStrategy = Field(default_factory=SearchStrategy)
    sessions_count: int = 0


class JobHunterState(TypedDict, total=False):
    """The complete graph state persisted by SqliteSaver."""
    candidate_profile: dict  # Serialized CandidateProfile
    applications: list       # List of serialized Application dicts
    feedback_log: list       # List of serialized FeedbackEvent dicts
    rejection_patterns: list # List of serialized Pattern dicts
    current_strategy: dict   # Serialized SearchStrategy
    session_count: int
    sessions_count: int      # Alias kept for requirement compatibility
    matched_jobs: list       # List of serialized JobPosting dicts
    pending_feedback_text: str  # Raw text from Gmail/manual paste awaiting parsing
    strategy_approved: bool     # Whether the user approved a proposed strategy change
    strategy_proposal: dict     # The proposed Pattern + action awaiting approval
    new_applications: list      # New applications added this session
    kpi_metrics: dict           # Computed KPIs for the dashboard
    strategy_change_log: list   # Explainable history of approved strategy updates
    usefulness_ratings: list    # Candidate feedback on pattern-detection usefulness
