# JobHunter — Feature Upgrade Spec
### Inspired by RightJob.ai · Grounded in Problem Statement 11 · Built for Vibe Coding

> **Ground rule:** Every feature below maps to a mandatory component, bonus challenge, or KPI 
> in the problem statement. Nothing here is cosmetic padding — each addition strengthens the 
> rubric score in a specific criterion. Criteria labels are called out per feature.

---

## TIER 1 — Core Upgrades (Do These First)
*These directly replace weak parts of the current prototype with something impressive.*

---

### 1. Match Score Engine → Replace plain ranking with a scored breakdown

**Inspired by:** RightJob.ai's "78% Good Match" with skill gap breakdown  
**Maps to:** `matcher` node (mandatory) + "Functional Correctness" rubric (30 marks)  
**What to build:**

The `matcher` node currently returns a single score. Replace it with a **three-axis breakdown**:

```python
class MatchScore(BaseModel):
    overall: float                  # 0–100, shown as "78% Good Match"
    experience_alignment: float     # Years of exp vs JD requirement
    skills_overlap: float           # Matched skills / total required skills
    industry_fit: float             # Candidate's domain vs company's domain
    missing_skills: list[str]       # ["Kubernetes", "Go"] — shown as skill gap
    match_label: Literal["Strong Match", "Good Match", "Partial Match", "Reach"]
```

**LLM prompt to add inside `matcher`:**
```
Given this job description and candidate profile, score alignment on three axes:
1. Experience Level (0-100): Does their YoE match the JD requirement?
2. Skills Overlap (0-100): What % of required skills does the candidate have?
3. Industry Fit (0-100): How relevant is their domain experience?

Also list up to 5 missing skills from the JD that the candidate lacks.
Return JSON only.
```

**UI change:** Each job card shows:
```
┌─────────────────────────────────────────────┐
│  Senior Backend Engineer — Stripe           │
│  ████████████░░  78% Good Match             │
│                                             │
│  Experience  ████████████  85%              │
│  Skills      ██████████░░  74%              │
│  Industry    ████████░░░░  65%              │
│                                             │
│  Missing: Kubernetes, Go, Distributed Sys  │
│  [Log Application]  [Ask Orion ✦]          │
└─────────────────────────────────────────────┘
```

**Why this is impressive:** The skill gap breakdown feeds directly into `pattern_detector`. 
If "Kubernetes" appears as a missing skill in 4 rejections, it surfaces as a pattern 
automatically. This creates a real data loop — not just a visual upgrade.

---

### 2. Skill Gap → Pattern Detection Pipeline (The Real Loop)

**Inspired by:** RightJob.ai's Skill Gap Analysis  
**Maps to:** `pattern_detector` + `strategy_updater` nodes (mandatory) + "LangGraph Mastery" rubric (20 marks)  
**What to build:**

Extend `FeedbackEvent` and `Pattern` to also capture **missing skills from match scores**, 
not just rejection text. This means pattern detection now has TWO signals:

```python
class FeedbackEvent(BaseModel):
    # existing fields ...
    missing_skills_at_application: list[str]   # from MatchScore at time of apply
    rejection_themes: list[str]                # from feedback text

class Pattern(BaseModel):
    # existing fields ...
    source: Literal["feedback_text", "skill_gap", "both"]
    # "both" = appeared in skill gap AND rejection feedback → high confidence
```

**New conditional edge:**
```python
def pattern_confidence_router(state):
    for pattern in state.rejection_patterns:
        if pattern.source == "both" and pattern.frequency >= 2:
            # Skill gap + rejection text both say the same thing
            # Trigger strategy update earlier (freq 2, not 3)
            return "strategy_updater"
    # Default: need freq >= 3 from text alone
    rejections = [e for e in state.feedback_log if e.outcome == "rejected"]
    if len(rejections) >= 3 and state.rejection_patterns:
        return "strategy_updater"
    return "state_saver"
```

**Why this is impressive:** You can justify to the panel *why* you have two pattern signals. 
"If both the job's skill requirements AND the rejection feedback point to the same gap, 
we're confident enough to act earlier." That's a real product decision, not just code.

---

### 3. Automated Filters Baked into `current_strategy`

**Inspired by:** RightJob.ai's seniority / work type / H1B filters  
**Maps to:** `SearchStrategy` state field (mandatory) + "Strategy update must change at least one search parameter visibly"  
**What to build:**

Extend `SearchStrategy` with filter fields that the `strategy_updater` can modify:

```python
class SearchStrategy(BaseModel):
    target_seniority: Literal["new_grad", "junior", "mid", "senior", "staff"]
    role_types: list[str]
    work_type: list[Literal["remote", "hybrid", "onsite"]]   # ADD THIS
    excluded_companies: list[str]
    prep_recommendations: list[str]
    max_results_per_session: int = 10
    # --- NEW ---
    min_match_score: float = 60.0    # Only show jobs above this threshold
    focus_skills: list[str] = []     # Prioritise jobs that need these skills (learning mode)
```

**Key behaviour:** When `strategy_updater` detects "Kubernetes gap", it adds `"Kubernetes"` 
to `focus_skills`. The `matcher` then boosts score for jobs that list Kubernetes — so 
the candidate actively builds toward filling the gap. This is the loop closing on itself.

**UI:** Strategy panel shows:
```
Current Strategy
────────────────
Seniority:   Mid-Level  (↓ adjusted from Senior)
Work Type:   Remote, Hybrid
Focus Skills: Kubernetes (+15% score boost)
Min Score:   65%

⚠ Strategy changed this session:
  "3 rejections cited Kubernetes gap. Boosting 
   Kubernetes roles to help you build experience."
```

---

## TIER 2 — "Orion" AI Co-pilot (The Showstopper Feature)

**Inspired by:** RightJob.ai's "Ask Orion" contextual Q&A  
**Maps to:** Bonus challenge "Resume-tailoring suggestions per role" (+4 marks) + "UI & UX" rubric (10 marks)  

> This is the feature that makes evaluators go "oh wow." It fits perfectly because the 
> problem statement says the agent should "surface specific preparation resources" — Orion 
> is just the conversational interface for that.

---

### 4. "Ask Orion" — Job-Contextual Q&A

**What to build:** A chat input that appears on each job card. It passes the job description 
+ candidate profile + current match score to the LLM and answers contextual questions.

```python
# New node: orion_chat (runs on-demand, not part of main graph flow)
# Triggered by UI interaction, not LangGraph edge

ORION_SYSTEM_PROMPT = """
You are Orion, a career co-pilot for a job seeker.
You have access to:
- The candidate's profile and skills
- A specific job description they're looking at  
- Their match score breakdown (overall, skills, experience, industry)
- Their application history and rejection patterns

Answer questions honestly and specifically. Examples:
- "Am I qualified?" → Use match score + missing skills
- "What's the culture like?" → Summarise from JD language and company signals
- "How should I prepare?" → Use detected patterns + missing skills
- "Should I apply?" → Weigh match score against their application strategy

Be direct. Don't hedge. If they're underqualified, say so and say why.
"""

def orion_chat(job: dict, candidate_state: JobHunterState, user_question: str) -> str:
    context = f"""
    Job: {job['title']} at {job['company']}
    Match Score: {job['match_score']['overall']}% ({job['match_score']['match_label']})
    Missing Skills: {job['match_score']['missing_skills']}
    Candidate Patterns: {[p.theme for p in candidate_state.rejection_patterns]}
    Question: {user_question}
    """
    # Call OpenRouter LLM with ORION_SYSTEM_PROMPT + context
```

**UI:** Below each job card:
```
┌─── Ask Orion about this role ───────────────┐
│  "Am I qualified for this senior role?"     │
│                                             │
│  Orion ✦: Your match score is 78%, but     │
│  you're missing Kubernetes and Go which     │
│  appear in 4 of your recent rejections.     │
│  I'd recommend applying but framing your    │
│  Docker experience as adjacent. Also prep   │
│  for a systems design round — it's your     │
│  current weak spot.                         │
└─────────────────────────────────────────────┘
```

**Why the panel will love this:** Orion is *using the persistent state*. It knows about 
the rejection patterns because they're in `JobHunterState`. It's not a generic chatbot — 
it's contextual because of LangGraph. That's the answer when they ask: 
*"Why does this need LangGraph?"*

---

### 5. "Why This Job Is A Match" — Auto-generated Per Card

**Inspired by:** RightJob.ai's personalized match summary  
**Maps to:** "matcher" node output displayed in UI  
**What to build:** After `matcher` scores a job, generate one sentence of reasoning:

```python
WHY_MATCH_PROMPT = """
In one sentence (max 20 words), explain why this job matches the candidate.
Focus on the strongest alignment signal. Be specific, not generic.

Bad: "This role aligns well with your background."
Good: "Your 4 years in fintech backend directly matches their core stack."
"""
```

This renders as a subtitle on each job card — zero extra LLM cost if batched with the 
scoring call.

---

## TIER 3 — Application Workflow (Bonus Challenges)

---

### 6. Resume Tailoring Suggestions Per Role

**Maps to:** Bonus challenge "Resume-tailoring suggestions per role" — problem statement  
**What to build:** A `resume_tailor` utility (NOT a full graph node — keep graph clean) 
called on-demand from UI:

```python
RESUME_TAILOR_PROMPT = """
Given this job description and the candidate's resume, suggest 3 specific changes 
to tailor the resume for this role.

Format:
1. [Section to edit] → [What to change] → [Why it helps]

Example:
1. [Skills section] → Add "Distributed Systems" explicitly → JD mentions it 5 times
2. [Experience bullet, Job 2] → Quantify the scale: "handled 10M requests/day" → matches their infra focus
3. [Summary] → Lead with "fintech backend" not "full-stack" → company is pure backend

Be surgical. No generic advice.
"""
```

**UI:** "Tailor Resume" button on each job card → opens a sidebar panel with the 3 suggestions.  
No file editing, no builder — just AI suggestions. Simple to build, impressive to demo.

---

### 7. Cover Letter Draft Per Application

**Maps to:** Bonus challenge "Cover letter drafts per application" — problem statement  
**What to build:** One-click cover letter generation baked into the application logging flow.

```python
COVER_LETTER_PROMPT = """
Write a 3-paragraph cover letter for this candidate applying to this role.

Paragraph 1: Hook — connect their strongest relevant experience to the company's mission.
Paragraph 2: Evidence — two specific achievements that map to the JD requirements.
Paragraph 3: Close — express genuine interest + reference one thing about the company specifically.

Tone: Confident, direct, human. Not corporate. Not sycophantic.
Max 250 words.
"""
```

Store the generated cover letter in the `Application` model:
```python
class Application(BaseModel):
    # existing fields ...
    cover_letter_draft: Optional[str] = None   # ADD THIS
    resume_tailoring_notes: Optional[list[str]] = None  # ADD THIS
```

---

## TIER 4 — Company Intelligence (Polish Layer)

**Inspired by:** RightJob.ai's Crunchbase integration  
**Complexity:** Low — just display enriched data from job dataset  

---

### 8. Company Signals on Job Cards

**What to build:** Add company metadata to the job dataset (or mock it) and display it:

```python
class CompanySignals(BaseModel):
    funding_stage: Optional[str]        # "Series B", "Public", "Bootstrapped"
    total_funding: Optional[str]        # "$45M"
    headcount_growth: Optional[str]     # "↑ 23% YoY" 
    recent_news_headline: Optional[str] # "Raised $20M Series B — March 2025"
    glassdoor_rating: Optional[float]   # 4.2
```

Add this to the job dataset CSV as extra columns. Even if mocked, it makes job cards 
look dramatically more useful and shows "business thinking" to the evaluator.

**UI display:**
```
Stripe · Series Unknown · Public
⭐ 4.5 Glassdoor · 7,000 employees
📰 "Stripe launches new payment APIs — April 2025"
```

---

## SUMMARY: What Each Feature Unlocks on the Rubric

| Feature | Rubric Criterion | Marks Impact |
|---|---|---|
| Match Score Breakdown (3-axis) | Functional Correctness | Core 30 marks — stronger matcher demo |
| Skill Gap → Pattern Pipeline | LangGraph Mastery | Core 20 marks — justifies the pattern choice |
| Extended SearchStrategy filters | Functional Correctness | Mandatory: "strategy must change visibly" |
| Ask Orion (contextual Q&A) | UI & UX + Demo | +10 marks potential (bonus) + 10 UI marks |
| "Why This Job Matches" summary | UI & UX | 10 marks — makes UI feel alive |
| Resume Tailoring Suggestions | Bonus challenges | +4 marks explicitly listed |
| Cover Letter Draft | Bonus challenges | +4 marks explicitly listed |
| Company Signals | Business Thinking | 10 marks — shows you thought about the product |

**Realistic total uplift: +15–20 marks on the rubric if Tier 1 + 2 are clean.**

---

## Build Order for Vibe Coding

```
Day 1 (Cleanup)
  └── Fix existing messy code, make graph run clean end-to-end

Day 2 (Tier 1)
  ├── Upgrade MatchScore model + matcher node prompt
  ├── Add missing_skills to FeedbackEvent
  └── Update pattern_confidence_router conditional edge

Day 3 (Tier 1 continued)
  ├── Extend SearchStrategy with focus_skills + work_type
  ├── Update strategy_updater to set focus_skills
  └── Update UI Strategy panel to show changes

Day 4 (Tier 2 — Orion)
  ├── Build orion_chat() utility function
  ├── Wire to UI: "Ask Orion" input per job card
  └── Add "Why This Job Matches" one-liner to matcher output

Day 5 (Tier 3 — Bonus)
  ├── resume_tailor() utility + UI button
  └── Cover letter draft + store in Application model

Day 6 (Tier 4 + Polish)
  ├── Add company signals to CSV + display in job cards
  ├── Record 3-session demo video
  └── Update ARCHITECTURE.md with new nodes/schema
```

---

## What NOT to Build (Scope Traps)

| RightJob.ai Feature | Why to Skip |
|---|---|
| Email Finder / LinkedIn URL scraper | Legal grey area; adds zero rubric marks |
| Autofill Applications | Requires browser extension — impossible in Streamlit |
| Outreach Credits system | Pure product feature, no AI angle, no rubric credit |
| Real Crunchbase API integration | Rate limits will kill your demo; mock it instead |
| Calendar integration | Only +4 bonus marks, high implementation risk |

---

*Load this file into your coding session. Build Tier 1 first — it's the foundation 
everything else sits on. Tier 2 is the demo moment. Tiers 3 & 4 are bonus marks if time allows.*
