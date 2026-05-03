import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from main import run_graph, get_user_state
from state import create_fresh_state, CandidateProfile, ApplicationStatus
from utils.auth import authenticate_user, register_user
from utils.cv_parser import extract_text_from_file, parse_cv_to_profile

st.set_page_config(
    page_title="JobHunter AI Coach",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom LMS CSS
st.markdown("""
<style>
    /* Global font and background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Login box styling */
    .login-box {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 40px;
        border-radius: 15px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        max-width: 450px;
        margin: auto;
        margin-top: 50px;
    }
    
    /* Coach Header */
    .coach-header {
        background: linear-gradient(135deg, #4b6cb7 0%, #182848 100%);
        padding: 25px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
    }
    .coach-header h1 {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        color: white;
    }
    
    /* Card Styling */
    .stContainer > div {
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        background-color: rgba(30, 30, 40, 0.5) !important;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .stContainer > div:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 36px;
        font-weight: 700;
        color: #4b6cb7;
    }
</style>
""", unsafe_allow_html=True)

# Authentication State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_name" not in st.session_state:
    st.session_state.user_name = None

# ---------------------------------------------------------
# LOGIN / REGISTER SCREEN
# ---------------------------------------------------------
if not st.session_state.authenticated:
    st.markdown("<div style='text-align: center; margin-top: 50px;'><h1 style='font-size: 48px;'>🎓 JobHunter AI</h1><p style='font-size: 18px; color: #aaa;'>Your Personal AI Career Coach</p></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        st.subheader("Login or Create Account")
        
        tab_login, tab_register = st.tabs(["Login", "Register"])
        
        with tab_login:
            log_user = st.text_input("Username", key="log_user")
            log_pin = st.text_input("PIN", type="password", key="log_pin")
            if st.button("Access Dashboard", type="primary", use_container_width=True):
                success, msg = authenticate_user(log_user, log_pin)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user_name = log_user
                    
                    # State Hydration
                    with st.spinner("Loading your career data..."):
                        history = get_user_state(log_user)
                        if history:
                            st.session_state["result"] = history
                            # Pre-fill profile
                            profile = history.get("candidate_profile")
                            if profile:
                                if not isinstance(profile, dict):
                                    profile = profile.model_dump()
                                st.session_state["profile_cache"] = profile
                    st.rerun()
                else:
                    st.error(msg)
                    
        with tab_register:
            reg_user = st.text_input("New Username", key="reg_user")
            reg_pin = st.text_input("New PIN", type="password", key="reg_pin")
            if st.button("Create Account", type="secondary", use_container_width=True):
                success, msg = register_user(reg_user, reg_pin)
                if success:
                    st.success("Account created! Please login.")
                else:
                    st.error(msg)
                    
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# MAIN DASHBOARD (LMS STYLE)
# ---------------------------------------------------------
else:
    # Top Header
    st.markdown(f"""
    <div class='coach-header'>
        <div>
            <h1>🎓 Welcome back, {st.session_state.user_name.capitalize()}!</h1>
            <span style='opacity: 0.8; font-size: 14px;'>Your AI Career Coach is ready to assist you.</span>
        </div>
        <div style='margin-left: auto;'>
            <div style='background: rgba(255,255,255,0.2); padding: 8px 15px; border-radius: 20px; font-weight: bold;'>
                🟢 Online
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hydrate form defaults if returning user
    p_cache = st.session_state.get("profile_cache", {})
    def_name = p_cache.get("name", st.session_state.user_name)
    def_skills = ", ".join(p_cache.get("skills", []))
    def_roles = ", ".join(p_cache.get("target_roles", []))
    def_exp = p_cache.get("experience_years", 0)
    def_loc = p_cache.get("location", "")
    def_edu = p_cache.get("education", "")

    with st.sidebar:
        st.title("👤 Candidate Profile")
        
        # CV Upload Section
        uploaded_cv = st.file_uploader("Upload CV to Auto-Fill (PDF/TXT)", type=["pdf", "txt"])
        if uploaded_cv is not None:
            if st.button("🪄 Auto-Fill from CV", use_container_width=True):
                with st.spinner("Extracting & analyzing CV via AI..."):
                    raw_text = extract_text_from_file(uploaded_cv)
                    if raw_text:
                        parsed_data = parse_cv_to_profile(raw_text)
                        if parsed_data:
                            # Update the profile cache so fields re-render with new defaults
                            p_cache.update(parsed_data)
                            st.session_state["profile_cache"] = p_cache
                            st.success("CV successfully analyzed! Please review the auto-filled fields below.")
                            st.rerun()
                        else:
                            st.error("Could not parse structured data from the CV.")
                    else:
                        st.error("Failed to extract text from the file.")
        
        st.markdown("---")
        
        name = st.text_input("Your Name", value=def_name)
        skills_text = st.text_area("Your Skills (comma separated)", value=def_skills, placeholder="Python, React, SQL")
        target_roles_text = st.text_area("Target Roles (comma separated)", value=def_roles, placeholder="Software Engineer, Backend Developer")
        experience_years = st.number_input("Years of Experience", min_value=0, max_value=30, value=int(def_exp))
        location = st.text_input("Location", value=def_loc, placeholder="New York, Remote")
        education = st.text_input("Education", value=def_edu, placeholder="B.Tech CS 2024")

        if st.button("🚀 Run Job Search", type="primary", use_container_width=True):
            skills = [s.strip() for s in skills_text.split(',')] if skills_text else []
            target_roles = [r.strip() for r in target_roles_text.split(',')] if target_roles_text else []
            
            profile = CandidateProfile(
                name=name,
                skills=skills,
                target_roles=target_roles,
                experience_years=experience_years,
                location=location,
                education=education
            )
            
            # If we already have a state, we use it, otherwise fresh
            input_dict = st.session_state.get("result", {})
            if not input_dict:
                state = create_fresh_state()
                input_dict = state.model_dump()
                
            input_dict["candidate_profile"] = profile.model_dump()
            
            with st.spinner("Analyzing profile & fetching jobs..."):
                result = run_graph(input_dict, thread_id=st.session_state.user_name)
                st.session_state["result"] = result
                st.session_state["profile_cache"] = profile.model_dump()
                
        if "result" in st.session_state:
            st.markdown("---")
            res = st.session_state["result"]
            st.metric("Total Applications", len(res.get("applications", [])))
            st.info(f"Session: {res.get('sessions_count', 1)}\n\nLast updated: {res.get('last_updated', '')}")
            
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user_name = None
            st.session_state.pop("result", None)
            st.session_state.pop("profile_cache", None)
            st.rerun()

    # SECTION 2 — MAIN AREA: 3 TABS
    tab1, tab2, tab3 = st.tabs([
        "🔍 Recommended Jobs", 
        "📁 Applications Log", 
        "🧠 Strategy & Patterns"
    ])

    # TAB 1: Recommended Jobs
    with tab1:
        if "result" not in st.session_state:
            st.info("Fill your profile in the sidebar and click 'Run Job Search' to begin your journey.")
        else:
            result = st.session_state["result"]
            jobs = result.get("recommended_jobs", [])
            st.subheader(f"Top {len(jobs)} Jobs Handpicked For You")
            
            for job in jobs:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    job_id = job.get('job_id', '') if isinstance(job, dict) else getattr(job, 'job_id', '')
                    title = job.get('title', '') if isinstance(job, dict) else getattr(job, 'title', '')
                    company_name = job.get('company_name', '') if isinstance(job, dict) else getattr(job, 'company_name', '')
                    loc = job.get('location', '') if isinstance(job, dict) else getattr(job, 'location', '')
                    exp_level = job.get('formatted_experience_level', '') if isinstance(job, dict) else getattr(job, 'formatted_experience_level', '')
                    remote = "Yes" if (job.get('remote_allowed') if isinstance(job, dict) else getattr(job, 'remote_allowed', False)) else "No"
                    salary = job.get('normalized_salary', 0) if isinstance(job, dict) else getattr(job, 'normalized_salary', 0)
                    match_score = job.get('match_score', 0) if isinstance(job, dict) else getattr(job, 'match_score', 0)
                    rank = job.get('rank', 0) if isinstance(job, dict) else getattr(job, 'rank', 0)

                    with col1:
                        st.write(f"### #{rank} {title}")
                        st.write(f"🏢 **{company_name}**")
                        st.write(f"📍 {loc} | 💼 {exp_level} | 🏠 Remote: {remote}")
                        if salary and float(salary) > 0:
                            st.write(f"💰 ${float(salary):,.0f}")
                        else:
                            st.write("💰 Salary not listed")
                        st.caption(f"🆔 Job ID: {job_id}")

                    with col2:
                        st.write("**Match Score**")
                        if match_score > 70:
                            st.markdown(f"<h1 style='color: #2ecc71; margin-top: -10px;'>{match_score}%</h1>", unsafe_allow_html=True)
                        elif match_score >= 40:
                            st.markdown(f"<h1 style='color: #f39c12; margin-top: -10px;'>{match_score}%</h1>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<h1 style='color: #e74c3c; margin-top: -10px;'>{match_score}%</h1>", unsafe_allow_html=True)

                        applications = result.get("applications", [])
                        already_applied = any(
                            str(app.get("job_id") if isinstance(app, dict) else getattr(app, "job_id", "")) == str(job_id)
                            for app in applications
                        )
                        if not already_applied:
                            already_applied = bool(job.get("user_applied", False)) if isinstance(job, dict) else getattr(job, "user_applied", False)
                        
                        if already_applied:
                            st.markdown(
                                """
                                <div style='
                                    background-color: #1a7a1a;
                                    color: white;
                                    padding: 10px 16px;
                                    border-radius: 8px;
                                    text-align: center;
                                    font-weight: bold;
                                    font-size: 15px;
                                    margin-top: 8px;
                                '>
                                ✅ Applied!
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            if st.button("🚀 Apply Now", key=f"apply_{job_id}", type="primary", use_container_width=True):
                                for j in jobs:
                                    j_id = (j.get("job_id") if isinstance(j, dict) else getattr(j, "job_id", ""))
                                    if str(j_id) == str(job_id):
                                        if isinstance(j, dict):
                                            j["user_applied"] = True
                                            j["user_feedback"] = ""
                                            j["feedback_type"] = "applied"
                                
                                name = st.session_state.user_name
                                input_dict = dict(result)
                                input_dict["recommended_jobs"] = jobs
                                
                                with st.spinner("Saving..."):
                                    new_result = run_graph(input_dict, thread_id=name)
                                    st.session_state["result"] = new_result
                                    st.rerun()
                st.write("") # spacer

    # TAB 2: Applications Log
    with tab2:
        if "result" not in st.session_state:
            st.info("Fill your profile and click Run Job Search")
        else:
            result = st.session_state["result"]
            applications = result.get("applications", [])
            
            if not applications:
                st.info("No applications tracked yet. Run a search first, then log your applications.")
            else:
                st.subheader(f"Your Applications ({len(applications)} total)")
                
                app_data = []
                for app in applications:
                    if isinstance(app, dict):
                        app_data.append({
                            "Company": app.get("company", ""),
                            "Role": app.get("role", ""),
                            "Status": app.get("status", ""),
                            "Applied Date": app.get("applied_date", ""),
                            "Notes": app.get("notes", "")
                        })
                    else:
                        app_data.append({
                            "Company": app.company,
                            "Role": app.role,
                            "Status": app.status.value if hasattr(app.status, 'value') else app.status,
                            "Applied Date": app.applied_date,
                            "Notes": app.notes
                        })
                
                df = pd.DataFrame(app_data)
                st.dataframe(df, use_container_width=True)
                
            st.markdown("---")
            st.subheader("📝 Log Interview / Rejection Feedback")
            st.write("Keep the AI coach updated on your progress to receive better strategies:")
            
            with st.form("feedback_form"):
                job_id_input = st.text_input("Job ID (from Recommended Jobs tab)")
                company_input = st.text_input("Company Name")
                feedback_text = st.text_area("Rejection/Interview Feedback (What went wrong? What went right?)")
                feedback_type = st.selectbox("Feedback Type", ["rejection", "interview", "offer"])
                submitted = st.form_submit_button("Log & Analyze", type="primary")
                
                if submitted and job_id_input and company_input:
                    current_result = st.session_state.get("result", {})
                    jobs = current_result.get("recommended_jobs", [])
                    
                    for job in jobs:
                        j_id = job.get("job_id") if isinstance(job, dict) else getattr(job, "job_id", "")
                        if str(j_id) == str(job_id_input):
                            if isinstance(job, dict):
                                job["user_applied"] = True
                                job["user_feedback"] = feedback_text
                                job["feedback_type"] = feedback_type
                                
                    name = st.session_state.user_name
                    input_dict = dict(current_result)
                    input_dict["recommended_jobs"] = jobs
                    
                    with st.spinner("Analyzing feedback and adjusting strategy..."):
                        new_result = run_graph(input_dict, thread_id=name)
                        st.session_state["result"] = new_result
                        st.success(f"Feedback logged for {company_input}!")
                        st.rerun()

    # TAB 3: Strategy & Patterns
    with tab3:
        if "result" not in st.session_state:
            st.info("Fill your profile and click Run Job Search")
        else:
            result = st.session_state["result"]
            strategy = result.get("current_strategy")
            patterns = result.get("rejection_patterns", [])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎯 Active Game Plan")
                if strategy:
                    if isinstance(strategy, dict):
                        seniority = strategy.get("seniority_level", "junior")
                        role_types = strategy.get("role_types", [])
                        locations = strategy.get("locations", [])
                        prep_resources = strategy.get("prep_resources", [])
                        notes = strategy.get("strategy_notes", "")
                    else:
                        seniority = getattr(strategy, "seniority_level", "junior")
                        role_types = getattr(strategy, "role_types", [])
                        locations = getattr(strategy, "locations", [])
                        prep_resources = getattr(strategy, "prep_resources", [])
                        notes = getattr(strategy, "strategy_notes", "")
                    
                    st.metric("Target Seniority", str(seniority).upper())
                    
                    if role_types:
                        st.write("**Target Roles:**")
                        for role in role_types:
                            st.write(f"  • {role}")
                            
                    if locations:
                        st.write("**Locations:**")
                        for loc in locations:
                            st.write(f"  • {loc}")
                            
                    if prep_resources:
                        st.write("**📚 Required Study Materials:**")
                        for res in prep_resources:
                            st.markdown(f"- {res}")
                            
                    if notes:
                        st.info(f"💡 **Coach's Note:**\n{notes}")
                        
            with col2:
                st.subheader("⚠️ Weakness Analysis")
                if not patterns:
                    st.success("✅ No recurring weaknesses detected yet. Keep applying!")
                else:
                    for pattern in patterns:
                        if isinstance(pattern, dict):
                            theme = pattern.get("theme", "")
                            freq = pattern.get("frequency", 0)
                            severity = pattern.get("severity", "")
                            status = pattern.get("status", "")
                            action = pattern.get("suggested_action", "")
                            resources = pattern.get("resources", [])
                        else:
                            theme = getattr(pattern, "theme", "")
                            freq = getattr(pattern, "frequency", 0)
                            severity = getattr(pattern, "severity", "")
                            status = getattr(pattern, "status", "")
                            action = getattr(pattern, "suggested_action", "")
                            resources = getattr(pattern, "resources", [])
                            
                        with st.container():
                            if status == "resolved":
                                st.success(f"✅ RESOLVED: {theme.title()}")
                            elif severity == "high":
                                st.error(f"🚨 HIGH PRIORITY: {theme.title()} (seen {freq} times)")
                            else:
                                st.warning(f"⚠️ WATCHLIST: {str(theme).title()} (seen {freq} times)")
                                
                            if action:
                                st.write(f"**Action Plan:** {action}")
                            if resources:
                                st.write("**Study Guide:**")
                                for res in resources:
                                    st.write(f"  📖 {res}")
                        st.write("")
