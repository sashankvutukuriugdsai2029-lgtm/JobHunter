"""
Profile Panel - Renders candidate profile styled like RightJob.ai reference.
"""

from __future__ import annotations

import streamlit as st
from src.profile_builder import save_profile_edits
from ui.components import render_skill_chips

def render_profile_panel(profile: dict, profile_key: str):
    st.markdown('<div class="profile-page-bg">', unsafe_allow_html=True)
    
    # Header Banner
    st.markdown('''
    <div style="display:flex; align-items:center; background:#EAFCF5; padding:12px 16px; border-radius:8px; margin-bottom:24px;">
        <span style="font-size:16px; margin-right:8px;">🛡️</span>
        <span style="font-size:13px; color:#1A1A1A; font-weight:600;">Your profile data is kept private and secure. ❓</span>
    </div>
    ''', unsafe_allow_html=True)

    tab_personal, tab_edu, tab_work, tab_skills, tab_equal = st.tabs([
        "Personal", "Education", "Work Experience", "Skills", "Equal Employment"
    ])
    
    with tab_personal:
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Personal Information</div>', unsafe_allow_html=True)
        with st.form("edit_personal_form"):
            new_name = st.text_input("Full Name", value=profile.get("name", ""))
            new_role = st.text_input("Target Role", value=profile.get("target_role", ""))
            
            curr_years = profile.get("years_experience", 0)
            has_exp = st.radio("Has work experience?", ["Yes", "None"], index=1 if curr_years == 0 else 0)
            if has_exp == "Yes":
                new_years = st.number_input("Years of Experience", min_value=0, max_value=50, value=max(1, curr_years), step=1)
            else:
                new_years = 0
                
            new_salary = st.text_input("Target Salary", value=profile.get("target_salary", ""))
            new_notes = st.text_area("Notes / Context", value=profile.get("notes", ""))
            
            if st.form_submit_button("Save Personal Info", type="primary"):
                updated = {
                    "name": new_name,
                    "target_role": new_role,
                    "years_experience": new_years,
                    "target_salary": new_salary,
                    "notes": new_notes
                }
                save_profile_edits(profile_key, updated)
                st.success("Personal information saved!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_edu:
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Education</div>', unsafe_allow_html=True)
        
        edu_list = profile.get("education", [])
        if edu_list:
            for edu in edu_list:
                st.markdown(f"**{edu.get('school', '')}** - {edu.get('degree', '')}")
        else:
            st.info("No education details added yet.")
            
        with st.expander("Add Education"):
            with st.form("add_edu_form", clear_on_submit=True):
                school = st.text_input("School / University")
                degree = st.text_input("Degree")
                if st.form_submit_button("Add", type="primary"):
                    if school:
                        new_edu = edu_list + [{"school": school, "degree": degree}]
                        save_profile_edits(profile_key, {"education": new_edu})
                        st.success("Education added!")
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_work:
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Work Experience</div>', unsafe_allow_html=True)
        
        work_list = profile.get("work_experience", [])
        if work_list:
            for work in work_list:
                st.markdown(f"**{work.get('title', '')}** at {work.get('company', '')}")
                if work.get("description"):
                    st.caption(work.get("description"))
        else:
            st.info("No work experience added yet.")
            
        with st.expander("Add Work Experience"):
            with st.form("add_work_form", clear_on_submit=True):
                title = st.text_input("Job Title")
                company = st.text_input("Company")
                description = st.text_area("Description")
                if st.form_submit_button("Add", type="primary"):
                    if title and company:
                        new_work = work_list + [{"title": title, "company": company, "description": description}]
                        save_profile_edits(profile_key, {"work_experience": new_work})
                        st.success("Work experience added!")
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_skills:
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Skills</div>', unsafe_allow_html=True)
        current_skills = profile.get("base_skills", [])
        
        if current_skills:
            st.markdown(render_skill_chips(current_skills), unsafe_allow_html=True)
        else:
            st.info("No skills added yet.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("edit_skills_form"):
            skills_str = st.text_input("Edit Skills (comma separated)", value=", ".join(current_skills))
            if st.form_submit_button("Save Skills", type="primary"):
                new_skills = [s.strip() for s in skills_str.split(",") if s.strip()]
                save_profile_edits(profile_key, {"base_skills": new_skills})
                st.success("Skills saved!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab_equal:
        st.markdown('<div class="profile-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Equal Employment</div>', unsafe_allow_html=True)
        
        eeo = profile.get("equal_employment", {})
        
        with st.form("edit_eeo_form"):
            gender = st.selectbox("Gender", ["Decline to Self-Identify", "Male", "Female", "Non-binary", "Other"], index=["Decline to Self-Identify", "Male", "Female", "Non-binary", "Other"].index(eeo.get("gender", "Decline to Self-Identify")))
            veteran = st.selectbox("Veteran Status", ["Decline to Self-Identify", "I am not a protected veteran", "I identify as one or more of the classifications of protected veteran"], index=["Decline to Self-Identify", "I am not a protected veteran", "I identify as one or more of the classifications of protected veteran"].index(eeo.get("veteran", "Decline to Self-Identify")))
            disability = st.selectbox("Disability Status", ["Decline to Self-Identify", "No, I don't have a disability", "Yes, I have a disability"], index=["Decline to Self-Identify", "No, I don't have a disability", "Yes, I have a disability"].index(eeo.get("disability", "Decline to Self-Identify")))
            
            if st.form_submit_button("Save Equal Employment Info", type="primary"):
                save_profile_edits(profile_key, {"equal_employment": {"gender": gender, "veteran": veteran, "disability": disability}})
                st.success("Equal Employment info saved!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
