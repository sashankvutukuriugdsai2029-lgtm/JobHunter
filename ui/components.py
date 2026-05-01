"""
Shared UI components for the JobHunter Streamlit dashboard.
Status badges, metric cards, and styling utilities.

Design system: Musmentor-inspired warm bento-card aesthetic.
"""

from __future__ import annotations

import streamlit as st


STATUS_COLORS = {
    "applied": "#3B82F6",
    "screening": "#F59E0B",
    "interviewing": "#10B981",
    "rejected": "#EF4444",
    "offer": "#22C55E",
}

STATUS_BG = {
    "applied": "rgba(59,130,246,0.10)",
    "screening": "rgba(245,158,11,0.10)",
    "interviewing": "rgba(16,185,129,0.10)",
    "rejected": "rgba(239,68,68,0.10)",
    "offer": "rgba(34,197,94,0.10)",
}

STATUS_ICONS = {
    "applied": "📤 Submitted",
    "screening": "🔍 Screening",
    "interviewing": "🎯 Interview",
    "rejected": "✗ Rejected",
    "offer": "★ Offer",
}

SENIORITY_COLORS = {
    "Junior": "#22C55E",
    "Mid-Level": "#F59E0B",
    "Senior": "#3B82F6",
}


def inject_custom_css():
    """Inject custom CSS for the warm bento-card dashboard."""
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Inter:wght@300;400;500;600;700&display=swap');

    /* ── Global ─────────────────────────────────── */
    .stApp {
        font-family: 'DM Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: #F5F0EB !important;
        color: #1A1A1A;
    }

    /* Remove default streamlit padding */
    .block-container {
        padding-top: 1.5rem !important;
    }

    /* ── Typography ─────────────────────────────── */
    h1, h2, h3 {
        font-family: 'DM Sans', sans-serif !important;
        letter-spacing: -0.02em;
        color: #1A1A1A;
    }

    .section-header {
        font-family: 'DM Sans', sans-serif;
        font-size: 24px;
        font-weight: 700;
        color: #1A1A1A;
        letter-spacing: -0.02em;
        margin-bottom: 6px;
    }

    .sub-header {
        font-size: 13px;
        color: #8C8278;
        margin-bottom: 18px;
        font-weight: 400;
    }

    /* ── Bento Cards ────────────────────────────── */
    .bento-card {
        background: #FFFCF9;
        border: 1px solid #E8E2DB;
        border-radius: 20px;
        padding: 22px 24px;
        box-shadow: 0 2px 12px rgba(120, 100, 70, 0.06);
        transition: box-shadow 0.25s ease, transform 0.2s ease;
    }

    .bento-card:hover {
        box-shadow: 0 6px 24px rgba(120, 100, 70, 0.10);
        transform: translateY(-1px);
    }

    .panel-card {
        background: #FFFCF9;
        border: 1px solid #E8E2DB;
        border-radius: 20px;
        padding: 20px 24px;
        box-shadow: 0 2px 12px rgba(120, 100, 70, 0.06);
    }

    /* ── Job Cards ──────────────────────────────── */
    .job-card {
        background: #FFFCF9;
        border: 1px solid #E8E2DB;
        border-radius: 18px;
        padding: 18px 20px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: border-color 0.25s ease, box-shadow 0.25s ease, transform 0.2s ease;
    }

    .job-card:hover {
        border-color: #E8734A;
        box-shadow: 0 6px 20px rgba(232, 115, 74, 0.10);
        transform: translateY(-1px);
    }

    .job-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 16px;
        font-weight: 600;
        color: #1A1A1A;
        margin-bottom: 4px;
        letter-spacing: -0.01em;
    }

    .job-company {
        font-size: 13px;
        color: #8C8278;
        margin-bottom: 6px;
    }

    /* ── Fit Score Bar ──────────────────────────── */
    .fit-score-bar {
        height: 6px;
        border-radius: 999px;
        background: #EDE8E3;
        overflow: hidden;
        margin-top: 8px;
    }

    .fit-score-fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.4s ease;
    }

    /* ── Badges ─────────────────────────────────── */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    .seniority-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 600;
        color: #FFFFFF;
    }

    /* ── Skill Chips ────────────────────────────── */
    .skill-chip {
        display: inline-block;
        background: #EAFCF5;
        border: none;
        padding: 6px 12px;
        border-radius: 8px;
        font-size: 13px;
        color: #1A1A1A;
        margin: 4px 6px 4px 0;
        font-weight: 500;
    }

    /* ── Metric / Stat Cards ────────────────────── */
    .metric-card {
        background: #FFFCF9;
        border: 1px solid #E8E2DB;
        border-radius: 18px;
        padding: 18px 16px;
        text-align: center;
        position: relative;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .metric-value {
        font-family: 'DM Sans', sans-serif;
        font-size: 28px;
        font-weight: 700;
        color: #1A1A1A;
        letter-spacing: -0.02em;
    }

    .metric-label {
        font-size: 12px;
        color: #8C8278;
        margin-top: 4px;
        font-weight: 500;
    }

    .metric-accent {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 2px;
        transform: rotate(45deg);
        margin-bottom: 8px;
    }

    /* ── Bento Stat (overview page) ─────────────── */
    .bento-stat {
        background: #FFFCF9;
        border: 1px solid #E8E2DB;
        border-radius: 20px;
        padding: 14px 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: box-shadow 0.25s ease;
    }

    @keyframes pulse-glow {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }

    .workflow-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }

    .workflow-dot.active {
        background: #22C55E;
    }

    .workflow-dot.pending {
        background: #F59E0B;
        animation: pulse-glow 1.5s ease-in-out infinite;
    }

    .empty-state {
        text-align: center;
        padding: 40px 20px;
        background: #FFFCF9;
        border: 2px dashed #E8E2DB;
        border-radius: 20px;
    }

    .empty-state-icon {
        font-size: 48px;
        margin-bottom: 12px;
    }

    .empty-state-title {
        font-size: 16px;
        font-weight: 600;
        color: #1A1A1A;
        margin-bottom: 6px;
    }

    .empty-state-sub {
        font-size: 13px;
        color: #8C8278;
    }

    .bento-stat:hover {
        box-shadow: 0 6px 20px rgba(120, 100, 70, 0.08);
    }

    .bento-stat-value {
        font-family: 'DM Sans', sans-serif;
        font-size: 36px;
        font-weight: 700;
        color: #1A1A1A;
        letter-spacing: -0.03em;
        line-height: 1;
    }

    .bento-stat-label {
        font-size: 12px;
        color: #8C8278;
        margin-top: 6px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .bento-stat-sub {
        font-size: 11px;
        color: #A89F95;
        margin-top: 8px;
    }

    /* ── Alert Box ──────────────────────────────── */
    .alert-box {
        background: #FFF5F0;
        border: 1px solid #F5D0C0;
        border-radius: 16px;
        padding: 16px 18px;
        margin: 10px 0;
    }

    /* ── Strategy Items ─────────────────────────── */
    .strategy-item {
        background: #FAF7F4;
        border: 1px solid #EDE8E3;
        border-radius: 14px;
        padding: 12px 14px;
        margin-bottom: 8px;
    }

    /* ── Next Steps ─────────────────────────────── */
    .next-step {
        border-left: 3px solid #E8734A;
        background: #FFF8F4;
        border-radius: 0 12px 12px 0;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 13px;
        color: #1A1A1A;
        font-weight: 500;
    }

    /* ── Sidebar Branding ──────────────────────── */
    .brand-wrap {
        text-align: center;
        padding: 8px 0 18px 0;
    }

    .brand-mark {
        width: 84px;
        height: 84px;
        border-radius: 16px;
        margin: 0 auto;
        background: linear-gradient(145deg, #E8734A 0%, #D4A574 50%, #C4956A 100%);
        display: block;
        object-fit: cover;
    }

    .brand-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: #1A1A1A;
        margin-top: 8px;
        letter-spacing: -0.02em;
    }

    .brand-sub {
        font-size: 12px;
        color: #8C8278;
        font-weight: 400;
    }

    /* ── Sidebar styling ───────────────────────── */
    section[data-testid="stSidebar"] {
        background: #FAF7F4 !important;
        border-right: 1px solid #E8E2DB !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
        border-radius: 999px !important;
        font-weight: 600 !important;
        font-family: 'DM Sans', sans-serif !important;
        letter-spacing: 0.01em;
        transition: all 0.2s ease !important;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: #1A1A1A !important;
        color: #FFFFFF !important;
        border: none !important;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
        background: #333333 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* ── Tab styling ───────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        background: #FFFCF9;
        border-radius: 14px;
        padding: 4px;
        border: 1px solid #E8E2DB;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500;
        font-size: 13px;
        border-radius: 10px;
        padding: 8px 16px;
        color: #8C8278;
    }

    .stTabs [aria-selected="true"] {
        background: #1A1A1A !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
    }

    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }

    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }

    /* ── Buttons in main content ────────────────── */
    .stButton > button {
        border-radius: 999px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }

    .stButton > button[kind="primary"] {
        background: #1A1A1A !important;
        color: #FFFFFF !important;
        border: none !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: #333333 !important;
    }

    .stButton > button[kind="secondary"],
    .stButton > button:not([kind="primary"]) {
        background: #FFFCF9 !important;
        border: 1px solid #E8E2DB !important;
        color: #1A1A1A !important;
    }

    .stButton > button[kind="secondary"]:hover,
    .stButton > button:not([kind="primary"]):hover {
        background: #FAF7F4 !important;
        border-color: #D4CFC8 !important;
    }

    /* ── Expander styling ──────────────────────── */
    .streamlit-expanderHeader {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
        border-radius: 14px !important;
        background: #FFFCF9 !important;
    }

    /* ── Selectbox / Input styling ──────────────── */
    .stSelectbox [data-baseweb="select"] > div {
        border-radius: 12px !important;
        border-color: #E8E2DB !important;
        background: #FFFCF9 !important;
    }

    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border-color: #E8E2DB !important;
        background: #FFFCF9 !important;
    }

    .stTextArea > div > div > textarea {
        border-radius: 12px !important;
        border-color: #E8E2DB !important;
        background: #FFFCF9 !important;
    }

    /* ── Radio styling ─────────────────────────── */
    .stRadio > div {
        gap: 6px !important;
    }

    /* ── Dataframe styling ─────────────────────── */
    .stDataFrame {
        border-radius: 14px !important;
        overflow: hidden;
    }

    /* ── Page header ───────────────────────────── */
    .page-header {
        padding: 0 0 14px 0;
    }

    .page-header h1 {
        margin: 0;
        font-family: 'DM Sans', sans-serif;
        font-size: 28px;
        font-weight: 700;
        color: #1A1A1A;
        letter-spacing: -0.03em;
    }

    .page-header p {
        margin: 4px 0 0 0;
        color: #8C8278;
        font-size: 14px;
    }

    .page-header .salary {
        font-size: 12px;
        color: #A89F95;
        margin-top: 2px;
    }

    /* ── Direction card ─────────────────────────── */
    .direction-card {
        background: #FFFCF9;
        border: 1px solid #E8E2DB;
        border-radius: 20px;
        padding: 24px;
    }

    .direction-label {
        font-size: 12px;
        color: #8C8278;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 500;
    }

    .direction-value {
        font-family: 'DM Sans', sans-serif;
        font-size: 24px;
        font-weight: 700;
        color: #1A1A1A;
        margin-top: 6px;
        letter-spacing: -0.02em;
    }

    .direction-meta {
        font-size: 12px;
        color: #A89F95;
        margin-top: 10px;
    }

    /* ── Proposal card ─────────────────────────── */
    .proposal-card {
        background: #FFF8F4;
        border: 2px solid #E8734A;
        border-radius: 20px;
        padding: 20px 22px;
    }

    .proposal-title {
        font-family: 'DM Sans', sans-serif;
        font-size: 16px;
        font-weight: 700;
        color: #C4570A;
    }

    .proposal-body {
        font-size: 13px;
        color: #5C534A;
        margin-top: 8px;
    }

    /* ── Chat styling ──────────────────────────── */
    .stChatMessage {
        border-radius: 16px !important;
    }

    /* ── Divider override ──────────────────────── */
    hr {
        border-color: #EDE8E3 !important;
    }

    /* ── Slider override ───────────────────────── */
    .stSlider [data-baseweb="slider"] [role="slider"] {
        background: #E8734A !important;
    }

    /* ── Success / Info / Warning messages ──────── */
    .stSuccess, .stAlert {
        border-radius: 14px !important;
    }

    /* ── Smooth scrollbar ──────────────────────── */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #F5F0EB;
    }
    ::-webkit-scrollbar-thumb {
        background: #D4CFC8;
        border-radius: 999px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #B5AFA8;
    }

    /* ── Profile Page Styles ────────────────────── */
    .profile-page-bg {
        background-color: #F8F9FA;
        padding: 24px;
        border-radius: 16px;
    }

    .profile-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 32px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 24px;
    }

    .profile-name {
        font-size: 28px;
        font-weight: 700;
        color: #1A1A1A;
        font-family: 'DM Sans', sans-serif;
        margin-bottom: 16px;
    }

    .social-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        background: #F8F9FA;
        border: 1px solid #EAEAEA;
        border-radius: 999px;
        font-size: 12px;
        color: #1A1A1A;
        font-weight: 500;
        margin: 0 8px 8px 0;
    }

    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #1A1A1A;
        font-family: 'DM Sans', sans-serif;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Timeline */
    .timeline {
        position: relative;
        padding-left: 24px;
        margin-bottom: 16px;
    }

    .timeline::before {
        content: '';
        position: absolute;
        top: 6px;
        bottom: 0;
        left: 6px;
        width: 2px;
        background: #EAEAEA;
    }

    .timeline-item {
        position: relative;
        margin-bottom: 24px;
    }

    .timeline-item:last-child {
        margin-bottom: 0;
    }

    .timeline-item::before {
        content: '';
        position: absolute;
        top: 6px;
        left: -23px;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #FFFFFF;
        border: 2px solid #10B981;
    }

    .timeline-date {
        font-size: 12px;
        color: #8C8278;
        margin-bottom: 4px;
        font-weight: 500;
    }

    .timeline-title {
        font-size: 15px;
        font-weight: 700;
        color: #1A1A1A;
        margin-bottom: 4px;
    }

    .timeline-subtitle {
        font-size: 13px;
        color: #5C534A;
        margin-bottom: 8px;
    }

    .timeline-content {
        font-size: 13px;
        color: #1A1A1A;
        line-height: 1.6;
    }

    .timeline-content ul {
        margin: 0;
        padding-left: 16px;
    }

    /* Right Sidebar Alert */
    .profile-alert {
        background: #FFF1F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }

    .profile-alert-icon {
        width: 24px;
        height: 24px;
        background: #FF4D4F;
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-bottom: 12px;
    }

    .profile-alert-text {
        font-size: 13px;
        color: #1A1A1A;
        margin-bottom: 16px;
        line-height: 1.5;
    }

    .profile-btn-black {
        display: block;
        width: 100%;
        padding: 10px;
        background: #1A1A1A;
        color: #FFFFFF;
        text-align: center;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 600;
        text-decoration: none;
    }
    
    .profile-menu-item {
        display: flex;
        justify-content: space-between;
        padding: 16px;
        background: #FFFFFF;
        border: 1px solid #EAEAEA;
        border-radius: 12px;
        margin-bottom: 8px;
        font-size: 13px;
        font-weight: 500;
        color: #1A1A1A;
    }
    </style>
    """, unsafe_allow_html=True)


def render_status_badge(status: str) -> str:
    """Return HTML for a colored status badge."""
    color = STATUS_COLORS.get(status, "#8C8278")
    bg = STATUS_BG.get(status, "rgba(140,130,120,0.10)")
    label = STATUS_ICONS.get(status, status.title())
    return f'<span class="status-badge" style="background: {bg}; color: {color};">{label}</span>'


def render_seniority_badge(seniority: str) -> str:
    """Return HTML for a seniority level badge."""
    color = SENIORITY_COLORS.get(seniority, "#8C8278")
    return f'<span class="seniority-badge" style="background: {color};">{seniority}</span>'


def render_fit_score_bar(score: float) -> str:
    """Return HTML for a fit score progress bar."""
    if score >= 70:
        color = "#22C55E"
    elif score >= 40:
        color = "#F59E0B"
    else:
        color = "#EF4444"

    return f'<div class="fit-score-bar"><div class="fit-score-fill" style="width: {min(score, 100)}%; background: {color};"></div></div>'


def render_skill_chips(skills: list) -> str:
    """Return HTML for skill chips."""
    chips = "".join(f'<span class="skill-chip">{s}</span>' for s in skills[:6])
    extra = len(skills) - 6
    if extra > 0:
        chips += f'<span class="skill-chip">+{extra} more</span>'
    return chips


def render_metric_card(value: str, label: str, color: str = "#E8734A") -> str:
    """Return HTML for a KPI metric card with diamond accent."""
    return f"""
    <div class="metric-card">
        <div class="metric-accent" style="background: {color};"></div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """


def render_bento_stat(value: str, label: str, sub: str = "", accent_color: str = "#E8734A") -> str:
    """Return HTML for a large bento stat card (overview page)."""
    sub_html = f'<div class="bento-stat-sub">{sub}</div>' if sub else ""
    return f"""
    <div class="bento-stat">
        <div class="metric-accent" style="background: {accent_color};"></div>
        <div class="bento-stat-value">{value}</div>
        <div class="bento-stat-label">{label}</div>
        {sub_html}
    </div>
    """
