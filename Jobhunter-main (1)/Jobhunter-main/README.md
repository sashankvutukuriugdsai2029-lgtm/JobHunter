# 🎓 JobHunter AI

JobHunter is a fully stateful, LangGraph-powered autonomous job hunting agent and career coach. Instead of just searching for jobs, JobHunter learns from your application history, analyzes your interview feedback, detects recurring weakness patterns, and dynamically adapts your job search strategy over time.

It features a sleek, premium **Learning Management System (LMS) style** Streamlit dashboard.

---

## 🚀 Key Features

### 🧠 Stateful LangGraph Architecture
JobHunter is built on a robust 9-node LangGraph pipeline that tracks your entire career journey:
1. **State Loader**: Initializes your session and retrieves persistent history from the SQLite database.
2. **Job Fetcher**: Curates jobs from a local database based on your active AI search strategy.
3. **Matcher**: Calculates custom Match Scores (0-100%) against your Candidate Profile.
4. **Ranker**: Ranks top recommendations dynamically.
5. **Application Tracker**: Persistently logs your applications.
6. **Feedback Parser**: Analyzes your interview/rejection feedback using LLMs to extract core themes.
7. **Pattern Detector**: Detects recurring weaknesses (e.g., if you fail "System Design" 3+ times).
8. **Strategy Updater**: Automatically downgrades target seniority or recommends specific study materials based on detected patterns.
9. **State Saver**: Safely checkpoints your graph state.

### 🪄 AI Resume Auto-Fill
Skip the manual data entry! Upload your CV (PDF or TXT) directly into the UI. JobHunter uses intelligent LLM extraction to automatically parse your Name, Top Skills, Target Roles, Years of Experience, Education, and Location to pre-fill your Candidate Profile.

### 🔐 Multi-User Authentication & Persistent Memory
JobHunter supports multiple users on the same machine.
- Register securely with a Username and PIN.
- The UI directly intercepts LangGraph's hidden checkpointer (SQLite) to **hydrate your session**.
- Log out and log back in days later, and your profile, active applications, and AI strategy will be exactly where you left them!

### 📊 LMS Career Coach Dashboard
A beautifully styled, glassmorphic UI built in Streamlit featuring:
- **Recommended Jobs Tab**: Live matched jobs with dynamic color-coded scores and instant "Apply Now" tracking.
- **Applications Log Tab**: A master table of your job pipeline, plus a dedicated form to log interview/rejection feedback.
- **Strategy & Patterns Tab**: A live dashboard showing your Coach's Active Game Plan and any high-priority watchlist weaknesses holding you back.

---

## 🛠️ Setup & Installation

### 1. Prerequisites
Ensure you have Python 3.9+ installed.

### 2. Install Dependencies
Install the required packages using pip:
```bash
pip install langgraph langgraph-checkpoint-sqlite streamlit pandas pydantic openai python-dotenv PyPDF2
```

### 3. Environment Variables
JobHunter uses OpenRouter to access reasoning-based LLMs (like `liquid/lfm-2.5-1.2b-thinking`). 
Create a `.env` file in the root directory:
```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=liquid/lfm-2.5-1.2b-thinking:free
```

### 4. Job Database
Ensure you have your sample jobs dataset located at `data/jobs.csv`.

---

## 🏃‍♂️ Running the Application

To launch the JobHunter Career Coach dashboard, run:
```bash
streamlit run ui/app.py
```

1. **Register**: Create a new account with a PIN.
2. **Upload CV**: Drag and drop your resume to auto-fill your profile, or fill it out manually.
3. **Run Search**: Click the primary button to trigger the LangGraph pipeline.
4. **Apply & Learn**: Apply to jobs, log fake (or real) rejection feedback, and watch the AI dynamically adapt your strategy!

---

## 📁 Project Structure

```text
jobhunter/
├── main.py                  # LangGraph compiler & runner
├── state.py                 # Pydantic schemas for the agent state
├── llm_client.py            # OpenRouter API wrapper
├── .env                     # API keys (not tracked)
├── jobhunter.db             # Auto-generated LangGraph SQLite checkpointer
├── README.md                # Project documentation
├── data/
│   ├── jobs.csv             # Job dataset
│   └── users.json           # Auto-generated user auth credentials
├── utils/
│   ├── auth.py              # User registration and PIN hashing
│   └── cv_parser.py         # PyPDF2 and LLM extraction logic
├── ui/
│   └── app.py               # Streamlit LMS Coach Dashboard
└── nodes/                   # The 9 core LangGraph nodes
    ├── state_loader.py
    ├── job_fetcher.py
    ├── matcher.py
    ├── ranker.py
    ├── application_tracker.py
    ├── feedback_parser.py
    ├── pattern_detector.py
    ├── strategy_updater.py
    └── state_saver.py
```
