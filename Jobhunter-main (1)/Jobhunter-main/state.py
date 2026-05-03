from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime

# Purpose: Defines all valid statuses an application can have
class ApplicationStatus(str, Enum):
    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    INTERVIEWING = "INTERVIEWING"
    REJECTED = "REJECTED"
    OFFER = "OFFER"

# Purpose: Stores everything about the job seeker
class CandidateProfile(BaseModel):
    name: str
    skills: List[str] = Field(default_factory=list)
    target_roles: List[str] = Field(default_factory=list)
    experience_years: int = 0
    education: str = ""
    location: str = ""
    resume_text: str = ""

# Purpose: Represents one single job application
class Application(BaseModel):
    job_id: str
    company: str
    role: str
    status: ApplicationStatus = ApplicationStatus.APPLIED
    applied_date: str = ""
    outcome_date: Optional[str] = None
    notes: str = ""

# Purpose: Stores one rejection or offer feedback entry
class FeedbackEvent(BaseModel):
    job_id: str
    company: str
    feedback_type: str = "rejection"
    feedback_text: str
    date: str = ""
    keywords_extracted: List[str] = Field(default_factory=list)

# Purpose: Represents one detected pattern from rejections
class Pattern(BaseModel):
    theme: str
    frequency: int = 1
    severity: str = "medium"
    first_detected: str = ""
    status: str = "active"
    suggested_action: str = ""
    resources: List[str] = Field(default_factory=list)

# Purpose: The agent's current job search game plan
class SearchStrategy(BaseModel):
    seniority_level: str = "junior"
    role_types: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    avoid_keywords: List[str] = Field(default_factory=list)
    prep_resources: List[str] = Field(default_factory=list)
    strategy_notes: str = ""

# Purpose: THE MASTER STATE — contains everything, flows through all nodes
class JobHunterState(BaseModel):
    candidate_profile: Optional[CandidateProfile] = None
    applications: List[Application] = Field(default_factory=list)
    feedback_log: List[FeedbackEvent] = Field(default_factory=list)
    rejection_patterns: List[Pattern] = Field(default_factory=list)
    current_strategy: Optional[SearchStrategy] = None
    sessions_count: int = 0
    recommended_jobs: List[dict] = Field(default_factory=list)
    session_summary: str = ""
    last_updated: str = ""

def create_default_strategy() -> SearchStrategy:
    return SearchStrategy(
        seniority_level="junior",
        role_types=["software", "developer", "engineer",
                    "analyst", "data"],
        locations=[],  # ← empty = no location filter
        strategy_notes="Initial default strategy — no patterns detected yet"
    )

def create_fresh_state() -> JobHunterState:
    return JobHunterState(
        current_strategy=create_default_strategy(),
        sessions_count=0,
        last_updated=str(datetime.now())
    )

if __name__ == "__main__":
    status_obj = ApplicationStatus.APPLIED
    profile_obj = CandidateProfile(name="Alice")
    app_obj = Application(job_id="1", company="TechCorp", role="SWE")
    feedback_obj = FeedbackEvent(job_id="1", company="TechCorp", feedback_text="Not enough experience")
    pattern_obj = Pattern(theme="Experience Level")
    strategy_obj = create_default_strategy()
    state_obj = create_fresh_state()
    
    print(f"Status: {status_obj}")
    print(f"Profile: {profile_obj}")
    print(f"Application: {app_obj}")
    print(f"Feedback: {feedback_obj}")
    print(f"Pattern: {pattern_obj}")
    print(f"Strategy: {strategy_obj}")
    print(f"State: {state_obj}")
    
    print("\nAll state classes working correctly!")
