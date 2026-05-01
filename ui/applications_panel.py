"""
Applications panel for the dashboard.
Tracks application progress and captures rejection feedback.
Warm bento-card design.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime

import streamlit as st

from ui.components import render_bento_stat, render_metric_card, render_status_badge


STATUSES = ["applied", "screening", "interviewing", "rejected", "offer"]


def _compute_kpi(applications: list[dict]) -> dict:
    counts = Counter(app.get("status", "applied") for app in applications)
    total = len(applications)
    interview_count = counts.get("interviewing", 0) + counts.get("offer", 0)
    conversion = round((interview_count / total) * 100, 1) if total else 0
    return {
        "total_applications": total,
        "interviewing": counts.get("interviewing", 0),
        "interview_conversion_rate": conversion,
        "offer": counts.get("offer", 0),
    }


def render_applications_panel(state: dict):
    """Render the applications tracker panel."""
    st.markdown('<div class="section-header">Application Tracker</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Update statuses, log rejection context, and monitor your pipeline health.</div>',
        unsafe_allow_html=True,
    )

    applications = list(state.get("applications", []))

    pending_apps = st.session_state.get("new_applications", [])
    if pending_apps:
        st.markdown(
            f"""
            <div class="bento-card" style="border-color:#F59E0B; background:#FFFBF0; margin-bottom:16px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:18px;">⏳</span>
                    <span style="font-size:13px; font-weight:500; color:#92400E;">
                        {len(pending_apps)} new application(s) waiting for the next agent run.
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not applications:
        st.markdown(
            """
            <div class="bento-card" style="text-align:center; padding:40px 24px;">
                <div style="font-size:36px; margin-bottom:12px;">📋</div>
                <div style="font-size:16px; font-weight:600; color:#1A1A1A; margin-bottom:6px;">
                    No applications tracked yet
                </div>
                <div style="font-size:13px; color:#8C8278;">
                    Add your first application from the Recommended Jobs tab.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    kpi = state.get("kpi_metrics") or _compute_kpi(applications)

    # KPI bento stat cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            render_bento_stat(str(kpi.get("total_applications", 0)), "Applications", accent_color="#E8734A"),
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            render_bento_stat(str(kpi.get("interviewing", 0)), "Interviewing", accent_color="#10B981"),
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            render_bento_stat(f"{kpi.get('interview_conversion_rate', 0)}%", "Interview Rate", accent_color="#F59E0B"),
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            render_bento_stat(str(kpi.get("offer", 0)), "Offers", accent_color="#22C55E"),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    counts = Counter(app.get("status", "applied") for app in applications)
    status_options = ["all"] + STATUSES
    selected_status = st.radio(
        "Filter by status",
        options=status_options,
        horizontal=True,
        format_func=lambda x: f"{x.title()} ({len(applications) if x == 'all' else counts.get(x, 0)})",
    )

    sort_choice = st.selectbox("Sort", options=["Newest first", "Oldest first", "Company A-Z"])

    filtered = applications
    if selected_status != "all":
        filtered = [a for a in filtered if a.get("status") == selected_status]

    if sort_choice == "Newest first":
        filtered = sorted(filtered, key=lambda x: x.get("date_applied", ""), reverse=True)
    elif sort_choice == "Oldest first":
        filtered = sorted(filtered, key=lambda x: x.get("date_applied", ""))
    else:
        filtered = sorted(filtered, key=lambda x: x.get("company_name", "").lower())

    st.caption(f"Showing {len(filtered)} of {len(applications)} applications")

    for i, app in enumerate(filtered):
        status = app.get("status", "applied")

        st.markdown(
            f"""
            <div class="job-card">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
                    <div>
                        <div class="job-title">{app.get('role_title', 'Unknown Role')}</div>
                        <div class="job-company">{app.get('company_name', 'Unknown Company')}</div>
                        <div style="font-size:12px; color:#A89F95; margin-top:4px;">
                            Applied: {app.get('date_applied', 'N/A')} · ID: {app.get('job_id', 'N/A')[:8]}
                        </div>
                    </div>
                    <div>{render_status_badge(status)}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Application Assets (Resume & Cover Letter)"):
            c_cl, c_res = st.columns(2)
            with c_cl:
                if app.get("cover_letter_draft"):
                    st.write("**Cover Letter Draft:**")
                    st.info(app["cover_letter_draft"])
                else:
                    if st.button("✨ Generate Cover Letter", key=f"cl_{app.get('job_id', i)}_{i}"):
                        with st.spinner("Drafting cover letter..."):
                            from src.resume_tailor import generate_cover_letter
                            job_data = next((j for j in state.get("matched_jobs", []) if j.get("job_id") == app.get("job_id")), {"title": app.get("role_title"), "company": app.get("company_name")})
                            cl = generate_cover_letter(job_data, state.get("candidate_profile", {}))
                            app["cover_letter_draft"] = cl
                            st.session_state.persistent_state["applications"] = applications
                            st.rerun()
            with c_res:
                if app.get("resume_tailoring_notes"):
                    st.write("**Resume Tailoring Suggestions:**")
                    for note in app["resume_tailoring_notes"]:
                        st.success(note)
                else:
                    if st.button("📝 Tailor Resume", key=f"res_{app.get('job_id', i)}_{i}"):
                        with st.spinner("Analyzing job description..."):
                            from src.resume_tailor import generate_resume_suggestions
                            job_data = next((j for j in state.get("matched_jobs", []) if j.get("job_id") == app.get("job_id")), {"title": app.get("role_title"), "company": app.get("company_name")})
                            notes = generate_resume_suggestions(job_data, state.get("candidate_profile", {}))
                            app["resume_tailoring_notes"] = notes
                            st.session_state.persistent_state["applications"] = applications
                            st.rerun()

        c1, c2 = st.columns([1, 1.2])
        with c1:
            new_status = st.selectbox(
                "Status",
                STATUSES,
                index=STATUSES.index(status) if status in STATUSES else 0,
                key=f"status_update_{app.get('job_id', i)}_{i}",
            )
            if st.button("Save status", key=f"save_status_{app.get('job_id', i)}_{i}", use_container_width=True):
                app["status"] = new_status
                app["date_last_updated"] = datetime.now().strftime("%Y-%m-%d")
                if new_status in ("rejected", "offer"):
                    app["date_outcome"] = app["date_last_updated"]
                st.session_state.persistent_state["applications"] = applications
                st.success("Status updated.")
                st.rerun()

        with c2:
            if status == "rejected":
                feedback = st.text_area(
                    "Rejection note",
                    placeholder="Paste rejection reason or summary...",
                    key=f"feedback_{app.get('job_id', i)}_{i}",
                    height=80,
                )
                if st.button("Log feedback", key=f"log_fb_{app.get('job_id', i)}_{i}", use_container_width=True):
                    if feedback.strip():
                        st.session_state.manual_feedback.append(
                            {
                                "app_id": app.get("job_id", ""),
                                "text": feedback.strip(),
                            }
                        )
                        st.success("Feedback added. Run agent to parse patterns.")
                        st.rerun()
                    else:
                        st.warning("Add feedback text before logging.")

    feedback_log = state.get("feedback_log", [])
    if feedback_log:
        st.markdown("---")
        st.markdown('<div class="section-header" style="font-size:18px;">Recent Parsed Feedback</div>', unsafe_allow_html=True)
        for fb in feedback_log[-5:]:
            st.markdown(
                f"""
                <div class="strategy-item">
                    <strong>{fb.get('extracted_reason', 'Unknown reason')}</strong><br>
                    <span style="font-size:11px; color:#A89F95;">
                        App: {fb.get('application_id', 'N/A')[:8]} · {fb.get('date_logged', '')}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
