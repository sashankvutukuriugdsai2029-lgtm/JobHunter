"""
Jobs panel for the dashboard.
Shows ranked jobs with filters and one-click apply actions.
Warm bento-card design.
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from ui.components import render_fit_score_bar, render_seniority_badge, render_skill_chips


def render_jobs_panel(state: dict):
    """Render the job feed panel."""
    st.markdown('<div class="section-header">Recommended Jobs</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Personalized matches ranked by fit score. Filter, inspect, and add to your tracker.</div>',
        unsafe_allow_html=True,
    )

    jobs = state.get("matched_jobs", [])
    strategy = state.get("current_strategy", {})

    if not jobs:
        st.markdown(
            """
            <div class="bento-card" style="text-align:center; padding:40px 24px;">
                <div style="font-size:36px; margin-bottom:12px;">🎯</div>
                <div style="font-size:16px; font-weight:600; color:#1A1A1A; margin-bottom:6px;">
                    No jobs loaded yet
                </div>
                <div style="font-size:13px; color:#8C8278;">
                    Run the agent from the sidebar to fetch personalized recommendations.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    target = strategy.get("target_seniority", "Senior")
    st.caption(f"🎯 Targeting: **{target}** roles")

    all_seniorities = sorted({j.get("seniority", "Unknown") for j in jobs})

    c1, c2, c3 = st.columns([1, 1, 1.2])
    with c1:
        min_score = st.slider("Minimum fit", min_value=0, max_value=100, value=45, step=5)
    with c2:
        seniority_filter = st.multiselect(
            "Seniority",
            options=all_seniorities,
            default=all_seniorities,
        )
    with c3:
        search_term = st.text_input("Keyword", placeholder="backend, python, fintech...").strip().lower()

    existing_apps = state.get("applications", [])
    existing_ids = {app.get("job_id") for app in existing_apps}
    pending_ids = {app.get("job_id") for app in st.session_state.get("new_applications", [])}

    filtered_jobs = []
    for job in jobs:
        score = float(job.get("fit_score", 0))
        seniority = job.get("seniority", "Unknown")
        haystack = " ".join(
            [
                str(job.get("title", "")),
                str(job.get("company", "")),
                str(job.get("description", "")),
                " ".join(job.get("required_skills", [])[:10]),
            ]
        ).lower()

        if score < min_score:
            continue
        if seniority_filter and seniority not in seniority_filter:
            continue
        if search_term and search_term not in haystack:
            continue
        filtered_jobs.append(job)

    st.caption(f"Showing {len(filtered_jobs)} of {len(jobs)} jobs")

    if not filtered_jobs:
        st.warning("No jobs match these filters. Lower the minimum fit or clear the keyword.")
        return

    for i, job in enumerate(filtered_jobs):
        score = float(job.get("fit_score", 0))
        match_score = job.get("match_score", {})
        skills = job.get("required_skills", [])
        score_color = "#22C55E" if score >= 70 else "#F59E0B" if score >= 40 else "#EF4444"
        seniority_html = render_seniority_badge(job.get("seniority", "Unknown"))
        skills_html = render_skill_chips(skills)
        
        # Format Company & Logo
        company_name = job.get('company', 'Unknown Company')
        logo_letter = company_name[0] if company_name else "U"
        
        # Details
        location = job.get("location", "Remote")
        if str(location) == "nan": location = "Remote"
        
        work_type = job.get('work_type', 'Full-time')
        if type(work_type) is list:
            work_type = work_type[0] if work_type else 'Full-time'
        if str(work_type) == "nan": work_type = "Full-time"
        work_type = work_type.title()
        
        pay = job.get("salary", "Not listed")
        if str(pay) == "nan" or not pay: pay = "Not listed"
        
        job_type = "Full-time"
        seniority = job.get('seniority', 'New Grad')

        # Match Box HTML
        match_box_html = ""
        if match_score:
            exp_score = match_score.get("experience_alignment", 0)
            skills_score = match_score.get("skills_overlap", 0)
            ind_score = match_score.get("industry_fit", 0)
            overall = int(score)
            match_label = match_score.get('match_label', 'GOOD MATCH').upper()
            
            match_box_html = f'<div style="background: #EAFCF5; border-radius: 12px; padding: 24px; width: 320px; flex-shrink: 0;"><div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 24px;"><div style="font-size: 48px; font-weight: 800; color: #1A1A1A; font-family: -apple-system, system-ui, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; line-height: 1;">{overall}<span style="font-size: 24px;">%</span></div><div style="font-size: 14px; font-weight: 700; color: #1A1A1A;">{match_label}</div></div><div style="background: #FFFFFF; border-radius: 8px; padding: 16px;"><div style="display: flex; justify-content: space-between; font-size: 14px; color: #1A1A1A; margin-bottom: 12px;"><span>Experience. Level</span><span style="font-weight: 700;">{int(exp_score)}<span style="font-size:10px; font-weight:600;">%</span></span></div><div style="display: flex; justify-content: space-between; font-size: 14px; color: #1A1A1A; margin-bottom: 12px;"><span>Skill</span><span style="font-weight: 700;">{int(skills_score)}<span style="font-size:10px; font-weight:600;">%</span></span></div><div style="display: flex; justify-content: space-between; font-size: 14px; color: #1A1A1A;"><span>Industry Exp.</span><span style="font-weight: 700;">{int(ind_score)}<span style="font-size:10px; font-weight:600;">%</span></span></div></div></div>'
        else:
            match_box_html = f'<div style="background: #EAFCF5; border-radius: 12px; padding: 24px; width: 320px; flex-shrink: 0;"><div style="font-size: 48px; font-weight: 800; color: #1A1A1A;">{int(score)}%</div></div>'

        # Build Main Card HTML (No newlines to prevent markdown parsing issues)
        card_html = f'<div style="background: #FFFFFF; border-radius: 16px; padding: 24px; border: 1px solid #EAEAEA; margin-bottom: 24px;"><div style="display: flex; gap: 32px;"><div style="flex: 1;"><div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;"><div style="width: 40px; height: 40px; background: #EAFCF5; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: #10B981; font-size: 20px;">{logo_letter}</div><div style="font-size: 16px; font-weight: 600; color: #1A1A1A;">{company_name}<span style="font-weight: 400; color: #1A1A1A;"> · Reposted 4 days ago</span></div></div><div style="font-size: 24px; font-weight: 700; color: #1A1A1A; margin-bottom: 24px; font-family: -apple-system, system-ui, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;">{job.get("title", "Untitled Role")}</div><div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; font-size: 15px; color: #1A1A1A; font-weight: 500;"><div><span style="margin-right: 8px;">📍</span>{location}</div><div><span style="margin-right: 8px;">⏱️</span>{job_type}</div><div><span style="margin-right: 8px;">🏠</span>{work_type}</div><div><span style="margin-right: 8px;">🎓</span>{seniority}</div><div><span style="margin-right: 8px;">💰</span>{pay}</div></div><div style="font-size: 15px; color: #1A1A1A; line-height: 1.5; margin-bottom: 24px;">{job.get("description", "No description available.")[:350]}...</div><div style="margin-bottom: 16px;">{skills_html}</div></div>{match_box_html}</div></div>'

        st.markdown(card_html, unsafe_allow_html=True)

        job_id = job.get("job_id", str(i))
        already_added = job_id in existing_ids or job_id in pending_ids

        b1, b2 = st.columns([1, 1.2])
        with b1:
            if st.button(
                "✓ Applied" if already_added else "Add Application →",
                key=f"apply_{job_id}_{i}",
                use_container_width=True,
                disabled=already_added,
            ):
                if "new_applications" not in st.session_state:
                    st.session_state.new_applications = []

                st.session_state.new_applications.append(
                    {
                        "job_id": job_id,
                        "company_name": job.get("company", ""),
                        "role_title": job.get("title", ""),
                        "status": "applied",
                        "date_applied": datetime.now().strftime("%Y-%m-%d"),
                        "date_last_updated": datetime.now().strftime("%Y-%m-%d"),
                        "date_outcome": "",
                        "missing_skills_at_application": match_score.get("missing_skills", []) if match_score else [],
                    }
                )
                st.success(f"Added {job.get('title', '')} at {job.get('company', '')} to queue.")
                st.rerun()

        with b2:
            description = (job.get("description") or "").strip()
            with st.expander("Show details"):
                st.write(description if description else "No job description available.")
                
