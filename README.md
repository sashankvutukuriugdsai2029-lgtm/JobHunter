# JobHunter: Persistent Candidate Search Assistant

## Overview
JobHunter is a stateful, long-running career copilot built with LangGraph and Streamlit. It tracks the full application lifecycle across sessions, learns from feedback, detects rejection patterns, and proposes strategy pivots.

## Problem
High-volume job seekers apply to many roles weekly, but most workflows are spreadsheet-driven and static. Rejection feedback is rarely synthesized into actionable strategy changes, and profile setup across tools is repetitive.

## Solution
JobHunter acts as a persistent memory agent:
1. Magic Onboarding: CV/document upload with LLM extraction into a candidate profile, strategy baseline, and target salary.
2. Dynamic Matching: Job recommendations from a local CSV dataset using evolving strategy and fit scoring.
3. Automated Tracking: Gmail integration for application-related emails and rejection parsing.
4. Strategy Pivot: Pattern detection over historical rejection data with human approval before strategy updates.
5. Agent Chat: Built-in LLM chat so users can communicate directly with their copilot.

## Target Users
- High-volume tech candidates applying to 10+ roles per week.
- Career pivoters calibrating role seniority.
- Candidates repeatedly blocked in specific interview stages.

## MVP Scope
- CV/doc onboarding with PDF + text ingestion.
- Multi-session persistence through LangGraph SqliteSaver.
- Stable local job feed from CSV/Kaggle-style dataset.
- Gmail OAuth integration for inbox scanning.
- Pattern detection threshold of 3+ historical feedback items.
- Core dashboard panels:
  - Job Feed
  - Application Tracker
  - Agent Strategy Log

## Tech Stack

### Core Logic & Agent Framework
- LangGraph (state machine + persistent checkpointer)
- Pydantic v2 (typed state models)
- LangChain + Gemini (LLM orchestration)

### Data Ingestion
- PyPDF2 (CV PDF text extraction)

### Persistence & Storage
- SQLite via LangGraph SqliteSaver (state memory)
- Local CSV + Pandas (job database)
- JSON profile stores (demo + user profiles)

### Frontend
- Streamlit

### Integrations
- Gmail API (OAuth 2.0)

## Data Storage
- Demo profiles: `data/demo_profiles.json`
- User-created profiles: `data/user_profiles.json`
- Graph checkpoint/state: `checkpoints/jobhunter.db`
- Env configuration: `.env` (including `OPENROUTER_API_KEY`)

## Running Locally
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Add backend key to `.env`:
   - `OPENROUTER_API_KEY=...`
3. Start app:
   - `streamlit run app.py`

## Notes
- Manual API-key entry is intentionally removed from UI.
- LLM features (profile extraction + chat) use backend environment configuration only.
