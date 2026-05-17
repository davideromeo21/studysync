import streamlit as st
import database
from config import (
    AVAILABLE_SUBJECTS, AVAILABLE_GOALS, AVAILABLE_STYLES,
    AVAILABLE_ENVIRONMENTS, AVAILABLE_VIBES, AVAILABLE_DEGREES,
)
from utils import get_avatar_url, calculate_profile_completion, invalidate_match_cache


def render():
    user_id = st.session_state.user_id
    user = database.get_user_by_id(user_id)
    completion = calculate_profile_completion(user)

    # ── Header ────────────────────────────────────────────────────────────────
    col_img, col_info = st.columns([1, 5])
    with col_img:
        avatar_url = get_avatar_url(user['username'])
        st.markdown(
            f'<img src="{avatar_url}" width="100" '
            f'style="border-radius:50%;border:3px solid #3b82f6;display:block;margin:auto;">',
            unsafe_allow_html=True,
        )
    with col_info:
        display_name = user.get('name') or user['username']
        degree = user.get('degree_level') or ""
        university = user.get('university') or ""
        sub_line = " · ".join(filter(None, [degree, university]))
        st.markdown(f"<h2 style='margin-bottom:2px;'>👤 {display_name}</h2>", unsafe_allow_html=True)
        if sub_line:
            st.markdown(f"<p style='color:#64748b;margin:0;'>{sub_line}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8;font-size:13px;margin:0;'>@{user['username']}</p>", unsafe_allow_html=True)

        # Profile completion bar
        color = "#10b981" if completion == 100 else ("#f59e0b" if completion >= 50 else "#3b82f6")
        st.markdown(
            f"<div style='margin-top:10px;'>"
            f"<span style='font-size:12px;color:#64748b;font-weight:600;'>Profile {completion}% complete</span>"
            f"<div class='profile-progress-bar'>"
            f"<div class='profile-progress-fill' style='width:{completion}%;background:{color};'></div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Tab completion indicators ──────────────────────────────────────────────
    missing_tab1 = sum([not user.get('name'), not user.get('course')])
    missing_tab2 = int(not user.get('subjects'))
    tab1_label = f"1️⃣  Basic Info {'⚠️' if missing_tab1 else '✅'}"
    tab2_label = f"2️⃣  Academic Needs {'⚠️' if missing_tab2 else '✅'}"
    tab3_label = "3️⃣  Study Preferences"

    with st.form("profile_form"):
        tab1, tab2, tab3 = st.tabs([tab1_label, tab2_label, tab3_label])

        with tab1:
            st.subheader("Basic Information")
            name = st.text_input(
                "Full Name *",
                value=user.get('name') or "",
                help="Your real name so study partners can recognize you.",
                placeholder="e.g. Alice Smith",
            )
            col1, col2 = st.columns(2)
            with col1:
                current_degree = user.get('degree_level')
                degree_index = (AVAILABLE_DEGREES.index(current_degree) + 1) if current_degree in AVAILABLE_DEGREES else 0
                degree_level = st.selectbox("Degree Level", options=[""] + AVAILABLE_DEGREES, index=degree_index)
                university = st.text_input("University", value=user.get('university') or "", placeholder="e.g. University of Lisbon")
            with col2:
                course = st.text_input(
                    "Degree / Course *",
                    value=user.get('course') or "",
                    help="e.g. BSc Computer Science",
                    placeholder="e.g. BSc Data Science",
                )
                campus = st.text_input("Campus", value=user.get('campus') or "", placeholder="e.g. Main Campus")
            submitted_t1 = st.form_submit_button("Save Profile", type="primary", use_container_width=True)

        with tab2:
            st.subheader("Academic Needs")
            subjects = st.multiselect(
                "Subjects you are studying *",
                options=AVAILABLE_SUBJECTS,
                default=[s for s in (user.get('subjects') or []) if s in AVAILABLE_SUBJECTS],
                help="Select all subjects you want to study with others.",
            )

            if subjects:
                st.subheader("Skill Levels")
                st.caption("Rate your current proficiency (1 = Beginner · 5 = Expert). Used to find mentors or advanced peers.")
                skill_levels = {}
                cols = st.columns(2)
                for i, subj in enumerate(subjects):
                    with cols[i % 2]:
                        current_val = (user.get('skill_levels') or {}).get(subj, 3)
                        skill_levels[subj] = st.slider(subj, min_value=1, max_value=5, value=current_val, key=f"skill_{subj}")
            else:
                skill_levels = {}
                st.info("Select subjects above to rate your skill levels.")

        with tab3:
            st.subheader("Study Preferences")
            goals = st.multiselect(
                "Primary Study Goals",
                options=AVAILABLE_GOALS,
                default=[g for g in (user.get('goals') or []) if g in AVAILABLE_GOALS],
                help="What are you trying to achieve in your study sessions?",
            )
            study_styles = st.multiselect(
                "Preferred Study Styles",
                options=AVAILABLE_STYLES,
                default=[s for s in (user.get('study_styles') or []) if s in AVAILABLE_STYLES],
                help="How do you learn best?",
            )

            st.subheader("Environment & Vibe")
            location_zone = st.text_input(
                "Location Zone / Neighbourhood",
                value=user.get('location_zone') or "",
                help="e.g. Downtown, North Campus",
                placeholder="e.g. City Centre",
            )
            study_environment = st.multiselect(
                "Preferred Study Environment",
                options=AVAILABLE_ENVIRONMENTS,
                default=[e for e in (user.get('study_environment') or []) if e in AVAILABLE_ENVIRONMENTS],
            )
            study_vibe = st.multiselect(
                "Study Vibe",
                options=AVAILABLE_VIBES,
                default=[v for v in (user.get('study_vibe') or []) if v in AVAILABLE_VIBES],
                help="What atmosphere do you prefer?",
            )
            # Save button inside Tab 3 — users don't have to scroll back to the bottom
            submitted_t3 = st.form_submit_button("Save Profile", type="primary", use_container_width=True)

        st.markdown("---")
        submitted_bottom = st.form_submit_button("Save Profile", type="primary", use_container_width=True)
        submitted = submitted_t1 or submitted_t3 or submitted_bottom

        if submitted:
            errors = []
            if not name.strip():
                errors.append("Full Name is required.")
            if not course.strip():
                errors.append("Degree / Course is required.")
            if not subjects:
                errors.append("Please select at least one subject.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                profile_data = {
                    'name': name.strip(),
                    'course': course.strip(),
                    'degree_level': degree_level or None,
                    'university': university.strip() or None,
                    'campus': campus.strip() or None,
                    'location_zone': location_zone.strip() or None,
                    'study_environment': study_environment,
                    'study_vibe': study_vibe,
                    'subjects': subjects,
                    'goals': goals,
                    'skill_levels': skill_levels,
                    'study_styles': study_styles,
                }
                success = database.update_user_profile(user_id, profile_data)
                if success:
                    database.log_activity(user_id, 'profile_saved', {})
                    invalidate_match_cache(user_id)
                    st.toast("Profile saved! Head to Matches & Groups to see updated scores.", icon="🎉")
                    st.rerun()
                else:
                    st.error("Failed to save profile. Please check your inputs and try again.")
