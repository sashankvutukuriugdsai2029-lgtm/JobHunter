"""
JobHunter - Persistent Candidate Search Assistant
Main Streamlit application entry point.

Run with: streamlit run app.py
"""

from __future__ import annotations

import os
import sys
import uuid
from collections import Counter

import streamlit as st
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

# ── LangSmith Tracing ────────────────────────────────────
# LangChain auto-detects these env vars and sends traces to LangSmith.
# If LANGCHAIN_API_KEY is missing, tracing is silently disabled.
_langsmith_key = os.environ.get("LANGCHAIN_API_KEY", "").strip()
if _langsmith_key and _langsmith_key != "your-langsmith-api-key-here":
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", "jobhunter")
    os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    _langsmith_active = True
else:
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    _langsmith_active = False

from src.gmail_client import fetch_rejection_emails
from src.graph import build_graph
from src.chat_agent import ask_agent
from src.profile_builder import create_or_update_user_profile, load_all_profiles
from ui.applications_panel import render_applications_panel
from ui.components import inject_custom_css, render_bento_stat, render_seniority_badge, render_status_badge
from ui.jobs_panel import render_jobs_panel
from ui.strategy_panel import render_strategy_panel


st.set_page_config(
    page_title="JobHunter - Career Copilot",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()


if "graph" not in st.session_state:
    graph, conn = build_graph()
    st.session_state.graph = graph
    st.session_state.db_conn = conn

if "new_applications" not in st.session_state:
    st.session_state.new_applications = []

if "manual_feedback" not in st.session_state:
    st.session_state.manual_feedback = []

if "strategy_approved" not in st.session_state:
    st.session_state.strategy_approved = False

if "strategy_rejected" not in st.session_state:
    st.session_state.strategy_rejected = False

if "agent_ran" not in st.session_state:
    st.session_state.agent_ran = False

if "persistent_state" not in st.session_state:
    st.session_state.persistent_state = {}
if "agent_chat_history" not in st.session_state:
    st.session_state.agent_chat_history = []


def load_profiles() -> dict:
    return load_all_profiles()


def run_agent(selected_key: str, profiles_data: dict):
    """Run the graph with merged state and persist the result."""
    graph = st.session_state.graph
    profile = profiles_data["profiles"][selected_key]
    default_strategy = profiles_data.get("default_strategies", {}).get(selected_key, {})

    prev = dict(st.session_state.persistent_state)
    prev_apps = prev.get("applications", [])
    new_apps = list(st.session_state.new_applications)

    pending_feedback = ""
    if st.session_state.manual_feedback:
        pending_feedback = "\n---\n".join(fb["text"] for fb in st.session_state.manual_feedback if fb.get("text"))

    input_state = {
        "candidate_profile": profile,
        "applications": prev_apps + new_apps,
        "feedback_log": prev.get("feedback_log", []),
        "rejection_patterns": prev.get("rejection_patterns", []),
        "current_strategy": prev.get("current_strategy") or default_strategy,
        "session_count": prev.get("session_count", 0),
        "sessions_count": prev.get("sessions_count", prev.get("session_count", 0)),
        "matched_jobs": [],
        "new_applications": new_apps,
        "pending_feedback_text": pending_feedback,
        "strategy_approved": st.session_state.strategy_approved,
        "strategy_proposal": prev.get("strategy_proposal", {}),
        "kpi_metrics": prev.get("kpi_metrics", {}),
        "strategy_change_log": prev.get("strategy_change_log", []),
        "usefulness_ratings": prev.get("usefulness_ratings", []),
        "interviews": prev.get("interviews", []),
    }

    thread_id = f"{selected_key}_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    with st.spinner("Running agent analysis..."):
        result = graph.invoke(input_state, config=config)

    st.session_state.persistent_state = dict(result)
    st.session_state.agent_ran = True
    st.session_state.new_applications = []
    st.session_state.manual_feedback = []
    st.session_state.strategy_approved = False
    st.session_state.strategy_rejected = False


def render_overview(state: dict, profile: dict):
    """Render high-level progress dashboard with compact stat ribbon."""
    applications = state.get("applications", [])
    kpi = state.get("kpi_metrics", {})
    patterns = state.get("rejection_patterns", [])
    proposal = state.get("strategy_proposal", {})
    matched_jobs = state.get("matched_jobs", [])

    if not kpi:
        counts = Counter(app.get("status", "applied") for app in applications)
        total = len(applications)
        interview_eligible = counts.get("interviewing", 0) + counts.get("offer", 0)
        offer_rate = round((counts.get("offer", 0) / interview_eligible) * 100, 1) if interview_eligible else 0.0
        kpi = {
            "total_applications": total,
            "interviewing": counts.get("interviewing", 0),
            "interview_conversion_rate": round((interview_eligible / total) * 100, 1) if total else 0,
            "offer": counts.get("offer", 0),
            "offer_rate": offer_rate,
        }

    queued_apps = len(st.session_state.get("new_applications", []))
    queued_feedback = len(st.session_state.get("manual_feedback", []))
    total_apps = kpi.get("total_applications", 0)

    # ── Compact Stat Ribbon ──────────────────────────
    st.markdown('<div class="section-header" style="font-size:16px; margin-bottom:8px;">Dashboard</div>', unsafe_allow_html=True)

    if total_apps == 0 and not matched_jobs:
        st.markdown('<div class="empty-state"><div class="empty-state-icon">🚀</div><div class="empty-state-title">Your pipeline is empty</div><div class="empty-state-sub">Upload a CV to build your profile, then click <strong>▶ Find job</strong> to see your first 5 ranked matches.</div></div>', unsafe_allow_html=True)
    else:
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(render_bento_stat(str(total_apps), "Apps", sub="Tracked", accent_color="#E8734A"), unsafe_allow_html=True)
        with m2:
            st.markdown(render_bento_stat(str(kpi.get("interviewing", 0)), "Interviews", sub="Active", accent_color="#10B981"), unsafe_allow_html=True)
        with m3:
            st.markdown(render_bento_stat(f"{kpi.get('interview_conversion_rate', 0)}%", "Conv. Rate", sub="Apps → Int.", accent_color="#F59E0B"), unsafe_allow_html=True)
        with m4:
            st.markdown(render_bento_stat(str(kpi.get("offer", 0)), "Offers", sub="Success", accent_color="#22C55E"), unsafe_allow_html=True)
        with m5:
            avg_days = kpi.get("avg_days_to_outcome")
            st.markdown(render_bento_stat("N/A" if avg_days is None else str(avg_days), "Avg Days", sub="To outcome", accent_color="#8B5CF6"), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ── Next Best Actions + Inline Run Agent ─────────
    col_left, col_right = st.columns([1.4, 1])

    with col_left:
        st.markdown('<div class="section-header" style="font-size:16px;">Next Best Actions</div>', unsafe_allow_html=True)

        next_steps = []
        if not matched_jobs:
            next_steps.append("🎯 Find job to generate the first batch of ranked jobs.")
        if queued_apps:
            next_steps.append(f"📥 Find job to ingest {queued_apps} newly added application(s).")
        if queued_feedback:
            next_steps.append(f"💬 Find job to parse {queued_feedback} pending feedback item(s).")
        if proposal and proposal.get("theme"):
            next_steps.append("🔄 Review the pending strategy pivot in Strategy Lab.")
        if patterns:
            next_steps.append("📊 Use detected patterns to update prep focus this week.")

        if next_steps:
            for step in next_steps:
                st.markdown(f'<div class="next-step">{step}</div>', unsafe_allow_html=True)
            if queued_apps > 0 or queued_feedback > 0 or not matched_jobs:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                is_profile_complete = bool(profile.get("name") and profile.get("target_role"))
                if st.button("▶ Find job", key="run_agent_main", use_container_width=True, type="primary", disabled=not is_profile_complete):
                    try:
                        run_agent(st.session_state.get("last_profile", ""), load_profiles())
                        st.success("Find job complete.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Agent error: {exc}")
        else:
            st.markdown('<div class="bento-card" style="text-align:center; padding:20px;"><div style="font-size:20px; margin-bottom:6px;">✅</div><div style="font-size:13px; font-weight:500; color:#1A1A1A;">Pipeline up to date</div><div style="font-size:11px; color:#8C8278;">No urgent actions pending.</div></div>', unsafe_allow_html=True)

        # ── Skill Gap Analysis ───────────────────────
        if matched_jobs:
            all_missing = []
            for j in matched_jobs:
                ms = j.get("match_score", {})
                all_missing.extend(ms.get("missing_skills", []))
            if all_missing:
                from collections import Counter as C2
                top3 = C2(all_missing).most_common(3)
                gap_chips = "".join(f'<span class="skill-chip" style="background:#FEE2E2; color:#991B1B;">{s} ({c}x)</span>' for s, c in top3)
                st.markdown(f'<div style="margin-top:12px;"><div style="font-size:13px; font-weight:600; color:#1A1A1A; margin-bottom:6px;">🎯 Top Missing Skills (from job pipeline)</div>{gap_chips}</div>', unsafe_allow_html=True)

        # ── Recent Applications Table ────────────────
        recent_apps = applications[-5:]
        if recent_apps:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            st.markdown('<div class="section-header" style="font-size:14px;">Recent Applications</div>', unsafe_allow_html=True)
            st.dataframe(
                [{"Company": a.get("company_name", ""), "Role": a.get("role_title", ""), "Status": a.get("status", ""), "Applied": a.get("date_applied", "")} for a in reversed(recent_apps)],
                use_container_width=True, hide_index=True,
            )

    with col_right:
        strategy = state.get("current_strategy", {})
        st.markdown(f'<div class="direction-card"><div class="direction-label">Current Direction</div><div class="direction-value">{strategy.get("target_seniority", "Senior")}</div><div class="direction-meta">Sessions: {state.get("session_count", state.get("sessions_count", 0))}</div><div class="direction-meta">Patterns: {len(patterns)}</div><div class="direction-meta">Pending: {queued_apps + queued_feedback}</div></div>', unsafe_allow_html=True)

        # ── Market Intelligence ──────────────────────
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        target_salary = st.session_state.get("persistent_state", {}).get("candidate_profile", {}).get("target_salary", "")
        seniority = strategy.get("target_seniority", "Senior")
        salary_ranges = {"Senior": "$140k – $195k", "Mid-Level": "$100k – $145k", "Junior": "$70k – $105k"}
        market_range = salary_ranges.get(seniority, "$90k – $160k")
        st.markdown(f'<div class="direction-card" style="border-color:#10B981;"><div class="direction-label">💰 Market Intelligence</div><div class="direction-meta" style="margin-top:6px;">Market range for <strong>{seniority}</strong> roles:</div><div style="font-size:20px; font-weight:700; color:#10B981; margin:6px 0;">{market_range}</div><div class="direction-meta">Your ask: <strong>{target_salary or "Not set"}</strong></div></div>', unsafe_allow_html=True)

        # Rejection pattern summary
        if patterns:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            for p in patterns[:2]:
                severity_icon = "🔴" if p.get("occurrences", 0) >= 5 else "🟠"
                st.markdown(f'<div class="alert-box" style="padding:12px 14px;"><div style="font-size:13px; font-weight:600; color:#C4570A;">{severity_icon} {p.get("theme", "")} <span style="font-weight:400; color:#A89F95;">({p.get("occurrences", 0)}x)</span></div></div>', unsafe_allow_html=True)

        # ── Upcoming Interviews ──────────────────────
        interviews = state.get("interviews", []) or st.session_state.persistent_state.get("interviews", [])
        if interviews:
            from datetime import datetime as dt_cls
            today = dt_cls.now().strftime("%Y-%m-%d")
            upcoming = sorted(
                [iv for iv in interviews if iv.get("interview_date", "") >= today],
                key=lambda x: (x.get("interview_date", ""), x.get("interview_time", "")),
            )[:3]

            if upcoming:
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                st.markdown('<div class="direction-card" style="border-color:#6366F1;"><div class="direction-label">📅 Upcoming Interviews</div>', unsafe_allow_html=True)
                for iv in upcoming:
                    type_icon = {"Phone Screen": "📞", "Video": "💻", "Onsite": "🏢", "Take-home": "📝"}.get(iv.get("interview_type", ""), "📅")
                    try:
                        iv_date = dt_cls.strptime(iv["interview_date"], "%Y-%m-%d")
                        days_until = (iv_date - dt_cls.now()).days
                        if days_until == 0:
                            countdown = "Today"
                        elif days_until == 1:
                            countdown = "Tomorrow"
                        elif days_until > 0:
                            countdown = f"in {days_until} days"
                        else:
                            countdown = "Past"
                    except (ValueError, KeyError):
                        countdown = ""

                    st.markdown(
                        f'<div style="background:#EEF2FF; border-radius:8px; padding:10px 12px; margin-top:8px;">'
                        f'<div style="font-weight:600; font-size:13px; color:#4338CA;">{type_icon} {iv.get("role", "Role")} at {iv.get("company", "Company")}</div>'
                        f'<div style="font-size:12px; color:#6366F1; margin-top:3px;">{iv.get("interview_date", "")} at {iv.get("interview_time", "")} · {iv.get("duration_minutes", 45)} min'
                        f' <span style="background:#C7D2FE; padding:2px 8px; border-radius:10px; font-weight:600; font-size:11px;">{countdown}</span></div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown('</div>', unsafe_allow_html=True)


def render_agent_chat(profile: dict, state: dict):
    st.markdown('<div class="section-header">Agent Chat</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Talk with your JobHunter copilot about strategy, applications, and next moves.</div>',
        unsafe_allow_html=True,
    )

    if not os.environ.get("GLM_API_KEY", "").strip():
        st.markdown(
            """
            <div class="bento-card" style="text-align:center; padding:28px 24px; border-color:#F59E0B;">
                <div style="font-size:24px; margin-bottom:8px;">🔑</div>
                <div style="font-size:14px; font-weight:500; color:#1A1A1A; margin-bottom:4px;">
                    Backend LLM key missing
                </div>
                <div style="font-size:13px; color:#8C8278;">
                    Set <code>GLM_API_KEY</code> in your <code>.env</code> file and restart the app.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for msg in st.session_state.agent_chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_message = st.chat_input("Ask your copilot anything about your job search...")
    if user_message:
        st.session_state.agent_chat_history.append({"role": "user", "content": user_message})
        with st.chat_message("user"):
            st.markdown(user_message)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = ask_agent(user_message, profile, state)
            st.markdown(reply)
        st.session_state.agent_chat_history.append({"role": "assistant", "content": reply})


profiles_data = load_profiles()
profile_options = {key: prof["name"] for key, prof in profiles_data["profiles"].items()}

# ── SIDEBAR ─────────────────────────────────────────────
with st.sidebar:
    import base64
    logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
    logo_base64 = ""
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <div class="brand-wrap">
            {"<img src='data:image/png;base64," + logo_base64 + "' class='brand-mark'>" if logo_base64 else "<div class='brand-mark'></div>"}
            <div class="brand-title">JobHunter</div>
            <div class="brand-sub">AI Career Copilot</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not profile_options:
        st.error("No profiles available. Create one below to continue.")

    # Apply deferred profile switch BEFORE the selectbox is created.
    # Streamlit forbids mutating a widget's session_state key after widget instantiation.
    pending_profile_switch = st.session_state.get("next_profile_key")
    if pending_profile_switch in profile_options:
        st.session_state.profile_selector = pending_profile_switch
        st.session_state.last_profile = pending_profile_switch
        st.session_state.persistent_state = {}
        st.session_state.new_applications = []
        st.session_state.manual_feedback = []
        del st.session_state["next_profile_key"]

    selected_key = st.selectbox(
        "Candidate profile",
        options=list(profile_options.keys()),
        format_func=lambda x: f"{profile_options[x]} ({profiles_data['profiles'][x].get('target_role', 'Role')})",
        key="profile_selector",
    )

    if "last_profile" not in st.session_state:
        st.session_state.last_profile = selected_key
    elif st.session_state.last_profile != selected_key:
        st.session_state.persistent_state = {}
        st.session_state.last_profile = selected_key
        st.session_state.new_applications = []
        st.session_state.manual_feedback = []

    selected_profile = profiles_data["profiles"].get(selected_key, {})
    skill_count = len(selected_profile.get("base_skills", []))
    st.caption(f"🛠 Skills tracked: {skill_count}")
    if selected_profile.get("target_salary"):
        st.caption(f"💰 Target salary: {selected_profile.get('target_salary')}")

    with st.expander("✨ Create New Profile", expanded=False):
        st.caption("Upload CV and related documents to build a new candidate profile.")

        with st.form("create_profile_form", clear_on_submit=False):
            create_name = st.text_input("Full name*")
            create_role = st.text_input("Target role*", value="Software Engineer")
            
            has_experience = st.radio("Has work experience?*", ["Yes", "None"])
            if has_experience == "Yes":
                create_years = st.number_input("Years of experience*", min_value=0, max_value=50, value=3, step=1)
            else:
                create_years = 0
                
            create_salary = st.text_input("Target salary (optional)", placeholder="$140k-$180k")
            create_notes = st.text_area(
                "Job search context",
                placeholder="Preferred industries, locations, salary range, job types, achievements...",
                height=90,
            )
            uploaded_files = st.file_uploader(
                "Upload CV / resume / job documents",
                type=["txt", "md", "csv", "json", "yaml", "yml", "log", "pdf"],
                accept_multiple_files=True,
            )

            submitted = st.form_submit_button("Create profile", use_container_width=True)

        if submitted:
            if not create_name.strip() or not create_role.strip():
                st.warning("Please add a profile name and target role.")
            else:
                with st.spinner("Building profile from your documents..."):
                    new_key, _, _, warnings = create_or_update_user_profile(
                        name=create_name,
                        target_role=create_role,
                        years_experience=int(create_years),
                        target_salary=create_salary,
                        additional_notes=create_notes,
                        uploaded_files=uploaded_files or [],
                        gemini_api_key=os.environ.get("GLM_API_KEY", ""),
                    )

                for warning in warnings:
                    st.info(warning)

                st.success("Profile created. Switched to your new profile.")
                st.session_state.next_profile_key = new_key
                st.rerun()

    state_snapshot = dict(st.session_state.persistent_state)
    session_count = state_snapshot.get("session_count", state_snapshot.get("sessions_count", 0))
    st.caption(f"📊 Sessions completed: {session_count}")

    is_profile_complete = bool(selected_profile.get("name") and selected_profile.get("target_role"))
    if st.button("▶ Find job", use_container_width=True, type="primary", disabled=not is_profile_complete):
        try:
            run_agent(selected_key, profiles_data)
            st.success("Find job complete.")
            st.rerun()
        except Exception as exc:
            st.error(f"Agent error: {exc}")

    st.markdown("---")
    st.markdown("### Workflow")
    jobs_count = len(state_snapshot.get('matched_jobs', []))
    apps_count = len(state_snapshot.get('applications', []))
    pending_apps = len(st.session_state.new_applications)
    pending_fb = len(st.session_state.manual_feedback)

    job_dot = "active" if jobs_count > 0 else "pending"
    app_dot = "active" if apps_count > 0 else "pending" if pending_apps > 0 else "active"
    fb_dot = "pending" if pending_fb > 0 else "active"

    st.markdown(f'<div style="line-height:2;"><span class="workflow-dot {job_dot}"></span> Jobs ranked: <strong>{jobs_count}</strong></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="line-height:2;"><span class="workflow-dot {app_dot}"></span> Tracked applications: <strong>{apps_count}</strong></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="line-height:2;"><span class="workflow-dot {"pending" if pending_apps > 0 else "active"}"></span> Pending new apps: <strong>{pending_apps}</strong></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="line-height:2;"><span class="workflow-dot {fb_dot}"></span> Pending feedback: <strong>{pending_fb}</strong></div>', unsafe_allow_html=True)

    # LangSmith tracing status
    if _langsmith_active:
        st.markdown('<div style="line-height:2;"><span class="workflow-dot active"></span> LangSmith: <strong>Tracing</strong></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="line-height:2;"><span class="workflow-dot pending"></span> LangSmith: <strong>Off</strong></div>', unsafe_allow_html=True)

    st.markdown("---")

    with st.popover("💬 Add Feedback", use_container_width=True):
        gmail_available = os.path.exists(os.path.join(os.path.dirname(__file__), "credentials.json"))
        if gmail_available:
            if st.button("📧 Scan Gmail", use_container_width=True, key="scan_gmail_pop"):
                with st.spinner("Scanning inbox..."):
                    emails = fetch_rejection_emails(max_results=5)
                if emails:
                    for email_text in emails:
                        st.session_state.manual_feedback.append({"app_id": "", "text": email_text})
                    st.success(f"Added {len(emails)} email(s).")
                else:
                    st.info("No relevant emails found.")
                st.rerun()

        manual_text = st.text_area(
            "Manual feedback",
            placeholder="Paste rejection text or interview notes.",
            key="sidebar_feedback",
            height=100,
        )
        if st.button("Queue Feedback", use_container_width=True, key="queue_fb_pop"):
            if manual_text.strip():
                st.session_state.manual_feedback.append({"app_id": "", "text": manual_text.strip()})
                st.success("Feedback queued.")
                st.rerun()
            else:
                st.warning("Add some text first.")

    with st.expander("Demo quick actions"):
        demo_rejections = [
            "We decided to move forward with candidates who demonstrated stronger system design skills.",
            "The system design round did not meet expectations for this role.",
            "Your system design approach did not align with our architecture standards.",
            "Coding skills were strong, but system design depth was below our bar.",
            "We are prioritizing candidates with broader systems experience.",
        ]

        if st.button("Add 3 system design rejections", use_container_width=True):
            for text in demo_rejections[:3]:
                st.session_state.manual_feedback.append({"app_id": "", "text": text})
            st.success("Added 3 demo feedback entries.")
            st.rerun()

        if st.button("Add 2 additional rejections", use_container_width=True):
            for text in demo_rejections[3:5]:
                st.session_state.manual_feedback.append({"app_id": "", "text": text})
            st.success("Added 2 demo feedback entries.")
            st.rerun()


# ── MAIN CONTENT ────────────────────────────────────────
current_state = dict(st.session_state.persistent_state)
selected_profile = profiles_data["profiles"][selected_key]

st.markdown(
    f"""
    <div class="page-header">
        <h1>JobHunter Workspace</h1>
        <p>
            Candidate: <strong>{selected_profile.get('name', '')}</strong> · Target role: {selected_profile.get('target_role', '')}
        </p>
        <p class="salary">
            Target salary: {selected_profile.get('target_salary', 'Not set')}
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

from ui.profile_panel import render_profile_panel

overview_tab, profile_tab, jobs_tab, apps_tab, strategy_tab, chat_tab = st.tabs(
    [
        "Overview",
        "Profile",
        "Recommended Jobs",
        "Applications",
        "Agent Strategy Log",
        "Agent Chat",
    ]
)

with overview_tab:
    render_overview(current_state, selected_profile)

with profile_tab:
    render_profile_panel(selected_profile, selected_key)

with jobs_tab:
    render_jobs_panel(current_state)

with apps_tab:
    render_applications_panel(current_state)

with strategy_tab:
    render_strategy_panel(current_state)

with chat_tab:
    render_agent_chat(selected_profile, current_state)


st.markdown("---")
st.caption("JobHunter v2 · Overview → Profile → Jobs → Applications → Strategy → Chat")
