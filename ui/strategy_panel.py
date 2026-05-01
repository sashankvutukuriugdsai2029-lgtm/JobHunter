"""
Strategy panel for the dashboard.
Explains the active strategy, detected patterns, and pending strategy decisions.
Warm bento-card design with orange accent highlights.
"""

from __future__ import annotations

import streamlit as st

from ui.components import render_seniority_badge


def render_strategy_panel(state: dict):
    """Render the strategy and pattern insights panel."""
    st.markdown('<div class="section-header">Agent Strategy Log</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Review what the agent learned, detected patterns, and approve or reject pivots.</div>',
        unsafe_allow_html=True,
    )

    strategy = state.get("current_strategy", {})
    patterns = state.get("rejection_patterns", [])
    proposal = state.get("strategy_proposal", {})
    session_count = state.get("session_count", state.get("sessions_count", 0))
    strategy_change_log = state.get("strategy_change_log", [])
    usefulness_ratings = state.get("usefulness_ratings", [])

    # ── Current Direction Card ──────────────────────────
    target_seniority = strategy.get("target_seniority", "Senior")
    work_type = ", ".join(strategy.get("work_type", ["remote", "hybrid", "onsite"])).title()
    min_score = strategy.get("min_match_score", 60.0)

    st.markdown(
        f"""
        <div class="direction-card">
            <div class="direction-label">Current Direction</div>
            <div class="direction-value">
                {render_seniority_badge(target_seniority)} {target_seniority} roles
            </div>
            <div class="direction-meta" style="margin-top:6px; color:#5C534A;">
                <strong>Work Type:</strong> {work_type} &nbsp;·&nbsp; <strong>Min Match Score:</strong> {min_score}%
            </div>
            <div class="direction-meta">Sessions completed: {session_count}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Focus Areas ─────────────────────────────────────
    focus = strategy.get("focus_areas", [])
    focus_skills = strategy.get("focus_skills", [])
    all_focus = focus + focus_skills
    if all_focus:
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-header" style="font-size:16px;">Focus Areas</div>', unsafe_allow_html=True)
        for area in focus:
            st.markdown(f'<div class="strategy-item">🎯 {area}</div>', unsafe_allow_html=True)
        for skill in focus_skills:
            st.markdown(f'<div class="strategy-item" style="border-left: 3px solid #E8734A;">⚡ <strong>{skill}</strong> (+15% score boost)</div>', unsafe_allow_html=True)

    # ── Preparation Plan ────────────────────────────────
    prep = strategy.get("prep_recommendations", [])
    if prep:
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="section-header" style="font-size:16px;">Preparation Plan</div>', unsafe_allow_html=True)
        for rec in prep:
            st.markdown(f'<div class="strategy-item">📚 {rec}</div>', unsafe_allow_html=True)

    # ── Detected Patterns ───────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-header" style="font-size:18px;">Detected Patterns</div>', unsafe_allow_html=True)

    if not patterns:
        feedback_count = len(state.get("feedback_log", []))
        if feedback_count < 3:
            st.markdown(
                f"""
                <div class="bento-card" style="text-align:center; padding:28px 24px;">
                    <div style="font-size:28px; margin-bottom:10px;">🔍</div>
                    <div style="font-size:14px; font-weight:500; color:#1A1A1A; margin-bottom:4px;">
                        Pattern detection requires 3 feedback entries
                    </div>
                    <div style="font-size:13px; color:#8C8278;">
                        Current progress: <strong>{feedback_count}/3</strong>
                    </div>
                    <div class="fit-score-bar" style="margin-top:12px; max-width:200px; margin-left:auto; margin-right:auto;">
                        <div class="fit-score-fill" style="width:{int(feedback_count/3*100)}%; background:#E8734A;"></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.success("No repeated negative pattern detected yet — your strategy is holding.")
    else:
        for pattern in patterns:
            occurrences = pattern.get("occurrences", 0)
            severity = "High" if occurrences >= 5 else "Medium"
            severity_icon = "🔴" if occurrences >= 5 else "🟠"
            color = "#C4570A" if occurrences >= 5 else "#92400E"
            bg = "#FFF0EB" if occurrences >= 5 else "#FFF5F0"

            st.markdown(
                f"""
                <div class="alert-box" style="background:{bg};">
                    <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                        <span style="font-size:14px;">{severity_icon}</span>
                        <span style="font-size:15px; font-weight:700; color:{color};">
                            {pattern.get('theme', 'Unknown Pattern')}
                        </span>
                        <span style="font-size:11px; color:#A89F95; font-weight:500;">
                            {severity} · {occurrences}x
                        </span>
                    </div>
                    <div style="font-size:13px; color:#5C534A;">
                        {pattern.get('proposed_action', 'Review and adjust strategy')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Pending Strategy Pivot ──────────────────────────
    if proposal and proposal.get("theme"):
        st.markdown("---")
        st.markdown('<div class="section-header" style="font-size:18px;">Pending Agent Recommendation</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="proposal-card">
                <div class="proposal-title">⚡ Strategy Pivot Proposed</div>
                <div class="proposal-body">
                    <strong>Theme:</strong> {proposal.get('theme', '')} · <strong>Occurrences:</strong> {proposal.get('occurrences', 0)}<br>
                    <strong>Proposed change:</strong> {proposal.get('proposed_action', '')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        a1, a2 = st.columns(2)
        with a1:
            if st.button("Approve Pivot →", key="approve_strategy", type="primary", use_container_width=True):
                st.session_state.strategy_approved = True
                st.success("Pivot approved. Run the agent to apply this strategy change.")
        with a2:
            if st.button("Reject Pivot", key="reject_strategy", use_container_width=True):
                st.session_state.strategy_approved = False
                st.session_state.strategy_rejected = True
                st.info("Pivot rejected. Current strategy remains active.")

    # ── Locked / Cooldown Changes ──────────────────────
    locked = strategy.get("locked_changes", [])
    if locked:
        st.markdown("---")
        st.markdown('<div class="section-header" style="font-size:16px;">Cooldown Changes</div>', unsafe_allow_html=True)
        positive_count = strategy.get("positive_events_since_last_change", 0)
        for change in locked:
            st.markdown(
                f'<div class="strategy-item">🔒 {change} <span style="font-size:11px; color:#A89F95;">(unlock: {positive_count}/3 positive events)</span></div>',
                unsafe_allow_html=True,
            )

    # ── Strategy Change History ─────────────────────────
    if strategy_change_log:
        st.markdown("---")
        st.markdown('<div class="section-header" style="font-size:16px;">Strategy Change History</div>', unsafe_allow_html=True)
        for entry in reversed(strategy_change_log[-3:]):
            changes = "; ".join(entry.get("changes", []))
            st.markdown(
                f"""
                <div class="strategy-item">
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
                        <span style="font-size:12px;">📅</span>
                        <strong style="font-size:13px;">{entry.get('date', '')} — {entry.get('theme', 'Pattern')}</strong>
                    </div>
                    <div style="font-size:12px; color:#5C534A;">{entry.get('proposed_action', '')}</div>
                    <div style="font-size:11px; color:#A89F95; margin-top:4px;">Applied: {changes}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Pattern Usefulness Rating ──────────────────────
    st.markdown("---")
    st.markdown('<div class="section-header" style="font-size:16px;">Pattern Detection Usefulness</div>', unsafe_allow_html=True)

    avg_usefulness = state.get("kpi_metrics", {}).get("pattern_usefulness_avg")
    if avg_usefulness is None and usefulness_ratings:
        avg_usefulness = round(sum(usefulness_ratings) / len(usefulness_ratings), 2)
    if avg_usefulness is not None:
        st.caption(f"Average rating: **{avg_usefulness}/5** from {len(usefulness_ratings)} response(s)")
    else:
        st.caption("No usefulness ratings yet.")

    rating = st.slider(
        "How useful were these pattern insights this session?",
        min_value=1,
        max_value=5,
        value=3,
        key="pattern_usefulness_slider",
    )
    if st.button("Save usefulness rating", use_container_width=True):
        ratings = list(st.session_state.persistent_state.get("usefulness_ratings", []))
        ratings.append(rating)
        st.session_state.persistent_state["usefulness_ratings"] = ratings
        st.success("Usefulness rating saved.")
        st.rerun()
