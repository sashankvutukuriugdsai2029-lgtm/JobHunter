# JobHunter — Architecture & Design Document
**Course:** UGDSAI 29 — Designing & Deploying AI Agents  
**Pattern:** Long-Running Stateful Workflow  
**LLM:** OpenRouter (OpenAI-compatible API)  
**Checkpointer:** SqliteSaver  

---

## 1. Problem Summary

Active job seekers apply to 50–100 roles over a month. They track applications in spreadsheets, tailor resumes manually, and lose track of which rejection feedback maps to which role. Existing job boards show listings but never *learn* from a candidate's evolving outcomes.

**JobHunter** is a stateful AI agent (built on LangGraph) that:
- Maintains the candidate's full search state across sessions
- Fetches and ranks new jobs against the candidate's evolving profile
- Tracks applications and parses rejection/offer feedback
- Detects recurring patterns in rejections (e.g., "failing system design rounds")
- Adapts the search strategy accordingly — adjusting seniority, role type, or recommending prep resources

---

## 2. LangGraph Pattern: Long-Running Stateful Workflow

### Why this pattern?

| Requirement | Why a simple chain fails | How LangGraph solves it |
|---|---|---|
| State persists across days/weeks | Chain has no memory between runs | `SqliteSaver` checkpoints full state to disk |
| Pattern detection needs 3+ historical events | Single prompt has no history | State accumulates `feedback_log` across sessions |
| Strategy adapts based on history | No conditional logic possible | Conditional edges route to `strategy_updater` only when patterns are detected |
| Candidate logs applications between sessions | No way to pause and resume | Graph resumes from checkpointed state each session |

---

## 3. Graph Architecture

### 3.1 Node Map

```
                        ┌─────────────┐
                        │ state_loader│  ← Loads SQLite checkpoint (or cold-starts)
                        └──────┬──────┘
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
        ┌─────────────┐ ┌────────────┐ ┌─────────────────────┐
        │ job_fetcher │ │  feedback  │ │ application_tracker │
        │             │ │  _parser   │ │                     │
        └──────┬──────┘ └─────┬──────┘ └──────────┬──────────┘
               │              │                   │
               ▼              ▼                   │
        ┌─────────────┐ ┌──────────────────┐      │
        │   matcher   │ │ pattern_detector │      │
        └──────┬──────┘ └────────┬─────────┘      │
               │                 │                │
               ▼                 ▼ (if ≥3 events) │
        ┌─────────────┐  ┌──────────────────┐     │
        │   ranker    │  │ strategy_updater │     │
        └──────┬──────┘  └────────┬─────────┘     │
               │                  │               │
               └──────────────────┴───────────────┘
                                  │
                           ┌──────▼──────┐
                           │ state_saver │  → Writes checkpoint to SQLite
                           └─────────────┘
```

### 3.2 Node Responsibilities

| Node | Responsibility | LLM Used? |
|---|---|---|
| `state_loader` | Loads `thread_id`-scoped checkpoint from SQLite; initialises cold state if first session | No |
| `job_fetcher` | Fetches new roles from job dataset/API matching `current_strategy` params (title, seniority, skills) | No |
| `matcher` | Scores each fetched job against `candidate_profile` and `preference_weights` | Yes (scoring prompt) |
| `ranker` | Sorts scored jobs, deduplicates against `seen_jobs`, returns top 10 | No |
| `application_tracker` | Receives candidate-entered applications (role, company, date, status) and appends to `applications` list | No |
| `feedback_parser` | Parses free-text rejection/offer/interview notes into a structured `FeedbackEvent` | Yes |
| `pattern_detector` | Examines `feedback_log` (min 3 events required); detects recurring themes using keyword scan + LLM | Yes |
| `strategy_updater` | Adjusts `current_strategy` (seniority, role_type, prep_resources) based on detected patterns | Yes |
| `state_saver` | Writes updated state to SQLite via `SqliteSaver`; increments `sessions_count` | No |

### 3.3 Conditional Edge Logic

```python
def should_update_strategy(state: JobHunterState) -> str:
    """
    Triggers strategy_updater only if:
    - pattern_detector found at least 1 pattern, AND
    - feedback_log has >= 3 rejection events
    """
    rejections = [e for e in state.feedback_log if e.outcome == "rejected"]
    if len(rejections) >= 3 and len(state.rejection_patterns) > 0:
        return "strategy_updater"
    return "state_saver"
```

---

## 4. State Schema (Pydantic v2)

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

class CandidateProfile(BaseModel):
    name: str
    resume_text: str
    target_roles: list[str]
    skills: list[str]
    years_of_experience: int
    preferred_locations: list[str]

class Application(BaseModel):
    job_id: str
    company: str
    role_title: str
    applied_date: datetime
    status: Literal["applied", "screening", "interviewing", "rejected", "offer"]
    notes: Optional[str] = None

class FeedbackEvent(BaseModel):
    job_id: str
    company: str
    outcome: Literal["rejected", "offer", "interview_scheduled", "no_response"]
    raw_feedback: str                    # candidate's free-text input
    parsed_themes: list[str]             # e.g. ["system design", "culture fit"]
    timestamp: datetime

class Pattern(BaseModel):
    theme: str                           # e.g. "system design weakness"
    frequency: int                       # how many times this appeared
    confidence: float                    # 0.0 – 1.0
    first_seen: datetime
    last_seen: datetime

class SearchStrategy(BaseModel):
    target_seniority: Literal["junior", "mid", "senior", "staff"]
    role_types: list[str]                # e.g. ["backend", "fullstack"]
    excluded_companies: list[str]
    prep_recommendations: list[str]      # e.g. ["Leetcode system design", "Grokking the SD Interview"]
    max_results_per_session: int = 10

class JobHunterState(BaseModel):
    candidate_profile: CandidateProfile
    applications: list[Application] = Field(default_factory=list)
    feedback_log: list[FeedbackEvent] = Field(default_factory=list)
    rejection_patterns: list[Pattern] = Field(default_factory=list)
    current_strategy: SearchStrategy
    sessions_count: int = 0
    seen_jobs: list[str] = Field(default_factory=list)   # job_ids already shown
    fetched_jobs: list[dict] = Field(default_factory=list)
    ranked_jobs: list[dict] = Field(default_factory=list)
```

---

## 5. Checkpointing & Session Persistence

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# Initialise once at app startup
checkpointer = SqliteSaver.from_conn_string("jobhunter.db")

# Thread ID = candidate ID (one thread per candidate)
config = {"configurable": {"thread_id": "candidate_001"}}

# Compile graph with checkpointer
app = graph.compile(checkpointer=checkpointer)

# Each session invokes the graph — state is auto-loaded and saved
result = app.invoke(session_input, config=config)
```

**How persistence works across sessions:**
1. Session 1 ends → `state_saver` writes full `JobHunterState` to `jobhunter.db`
2. App restarts (or next day begins)
3. Session 2 starts → `state_loader` reads the checkpointed state from SQLite
4. `sessions_count` increments, `seen_jobs` prevents re-showing old listings
5. Pattern detection now has Session 1's feedback to work with

---

## 6. Pattern Detection Logic

Pattern detection is gated — it only fires after **3 or more rejection feedback events**.

### Keyword-Based (Minimum Requirement)
```python
REJECTION_KEYWORDS = {
    "system design": ["system design", "architecture", "scalability", "design round"],
    "coding": ["leetcode", "coding test", "algorithm", "data structures"],
    "communication": ["communication", "articulation", "presentation skills"],
    "culture fit": ["culture fit", "values", "team fit"],
    "experience gap": ["overqualified", "underqualified", "experience level"],
}
```

### LLM-Based (Bonus — implemented on top of keyword scan)
```python
PATTERN_DETECTION_PROMPT = """
You are analysing a job seeker's rejection feedback log.

Feedback events:
{feedback_events}

Identify recurring themes that appear in 2 or more rejections.
Return a JSON list of patterns with fields: theme, frequency, confidence (0-1).
Only return patterns with confidence >= 0.6.
"""
```

### Strategy Change Rules

| Detected Pattern | Strategy Adjustment |
|---|---|
| `system design weakness` (freq ≥ 2) | Add "Grokking System Design" to `prep_recommendations`; drop seniority one level |
| `coding test failure` (freq ≥ 2) | Add "NeetCode 150" to `prep_recommendations` |
| `experience gap — overqualified` (freq ≥ 2) | Drop seniority one level |
| `experience gap — underqualified` (freq ≥ 2) | Raise seniority one level |
| `culture fit` (freq ≥ 3) | Add "culture fit interview prep" to `prep_recommendations` |

Strategy changes are **always logged with a human-readable explanation**, visible in the Streamlit UI.

---

## 7. Data Flow Per Session

```
Session Start
    │
    ├─► state_loader      → loads JobHunterState from SQLite (or cold-starts)
    │
    ├─► job_fetcher       → queries job dataset with current_strategy params
    │       └── fetched_jobs: list[dict]
    │
    ├─► matcher           → LLM scores each job vs candidate_profile
    │       └── scored_jobs: list[dict] with match_score
    │
    ├─► ranker            → deduplicates, sorts, returns top 10
    │       └── ranked_jobs: list[dict]
    │
    ├─► application_tracker → candidate logs new applications via UI
    │       └── applications: list[Application] updated
    │
    ├─► feedback_parser   → candidate enters rejection/offer notes
    │       └── feedback_log: list[FeedbackEvent] updated
    │
    ├─► pattern_detector  → scans feedback_log (if ≥ 3 rejections)
    │       └── rejection_patterns: list[Pattern]
    │
    ├─► strategy_updater  → (conditional) adjusts current_strategy
    │       └── current_strategy updated + explanation logged
    │
    └─► state_saver       → checkpoints full state to SQLite
```

---

## 8. Streamlit UI — Three Panel Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  JobHunter  |  Session #3  |  Candidate: John Doe                  │
├──────────────────────┬──────────────────────┬───────────────────────┤
│  PANEL 1: JOBS       │  PANEL 2: APPLICATIONS│  PANEL 3: STRATEGY   │
│                      │                      │                       │
│  Top 10 matches      │  Application log     │  Current strategy     │
│  this session        │  with status badges  │  (seniority, roles)   │
│                      │  ● Applied (3)       │                       │
│  [Job cards with     │  ● Screening (1)     │  Detected patterns:   │
│   match score]       │  ● Rejected (2)      │  ⚠ System design      │
│                      │  ● Interviewing (1)  │    weakness (2x)      │
│  [Log Application]   │  ● Offer (0)         │                       │
│  button per job      │                      │  Strategy changes:    │
│                      │  [Add Feedback]      │  ↓ Seniority: Senior  │
│                      │  button per app      │    → Mid-level        │
│                      │                      │  + Prep: Grokking SD  │
└──────────────────────┴──────────────────────┴───────────────────────┘
```

---

## 9. Demo Flow (3 Sessions)

### Session 1 — Cold Start
- Agent cold-starts with resume input
- `job_fetcher` pulls 10 roles matching resume skills
- Candidate logs 5 applications
- Candidate enters feedback: 2 rejections — both mention "system design"
- `pattern_detector` runs but threshold not met (only 2 events) → no strategy change
- State saved: `sessions_count = 1`

### Session 2 — Pattern Detected
- State loaded: 2 prior rejections visible
- Candidate logs 1 more rejection — again mentions "system design round"
- `pattern_detector` now has 3 events → threshold met
- Pattern: `system design weakness` (freq=3, confidence=0.85)
- `strategy_updater` fires:
  - Seniority: `senior` → `mid`
  - Prep added: `["Grokking the System Design Interview", "ByteByteGo"]`
  - UI shows explanation: *"3 rejections cited system design. Adjusting to mid-level roles and recommending prep resources."*
- State saved: `sessions_count = 2`

### Session 3 — Strategy Adaptation Visible
- State loaded: strategy already adjusted
- New job recommendations reflect mid-level seniority
- Candidate logs 2 new applications (from new strategy)
- Candidate reports 1 interview scheduled (no rejection)
- Pattern frequency stays at 3 — no further downgrade
- UI shows: Strategy holding at mid-level, prep resources still active

---

## 10. Tech Stack

| Component | Technology |
|---|---|
| Agent Framework | LangGraph (latest stable) |
| LLM | OpenRouter (OpenAI-compatible endpoint) |
| State Schema | Pydantic v2 `BaseModel` |
| Checkpointer | `SqliteSaver` → `jobhunter.db` |
| UI | Streamlit |
| Job Data | Kaggle job postings dataset / static CSV |
| Version Control | Git + GitHub |
| Language | Python 3.10+ |

---

## 11. Key Design Decisions & Trade-offs

| Decision | Chosen Approach | Alternative Considered | Reason |
|---|---|---|---|
| Checkpointer | SqliteSaver | PostgresSaver | Simpler setup for 14-day scope; no infra needed |
| LLM Provider | OpenRouter | Direct OpenAI | Cost flexibility; can swap models without code change |
| Pattern detection trigger | ≥ 3 rejection events | Every session | Avoids premature strategy changes on sparse data |
| Job data source | Static CSV + Kaggle dataset | Live API scraping | Reliability in demo; avoids rate-limit failures |
| Strategy change visibility | Explicit UI panel with explanation | Silent background update | Rubric requires strategy changes to be "explainable in UI" |

---

## 12. Submission Checklist Reference

- [x] LangGraph graph with all 9 required nodes
- [x] Pydantic v2 `JobHunterState` with all required fields  
- [x] `SqliteSaver` persistent checkpointer
- [x] ≥ 5 application statuses: `applied`, `screening`, `interviewing`, `rejected`, `offer`
- [x] Pattern detection gates on ≥ 3 historical events
- [x] Strategy update changes ≥ 1 search parameter visibly in UI
- [x] Streamlit UI with 3 panels: jobs / applications log / strategy & patterns
- [x] Demo covers 3+ sessions with evolving state
- [x] `graph.get_graph().draw_png()` state diagram committed to repo
- [x] Pre-recorded 3-minute demo video
- [x] Business memo (one page PDF/MD)
- [x] README with setup, env vars, architecture reference, data source citations
