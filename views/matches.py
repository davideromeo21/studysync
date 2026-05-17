import streamlit as st
import database
from matcher import MatcherService
import plotly.graph_objects as go
from icalendar import Calendar, Event
from datetime import datetime, timedelta, date
from config import AVAILABLE_SUBJECTS, DAYS, TIMESLOTS, SLOT_ICONS, score_color, score_label
from utils import get_avatar_url


# ── Chart helpers ─────────────────────────────────────────────────────────────

def create_radar_chart(u1: dict, u2: dict, shared_subjects: list):
    if not shared_subjects:
        return None
    categories = list(shared_subjects)
    u1_skills = [u1.get('skill_levels', {}).get(s, 3) for s in categories]
    u2_skills = [u2.get('skill_levels', {}).get(s, 3) for s in categories]
    categories_closed = categories + [categories[0]]
    u1_closed = u1_skills + [u1_skills[0]]
    u2_closed = u2_skills + [u2_skills[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=u1_closed, theta=categories_closed, fill='toself',
        name=u1.get('name') or u1['username'],
        line=dict(color='#3b82f6', width=2),
        fillcolor='rgba(59,130,246,0.15)',
    ))
    fig.add_trace(go.Scatterpolar(
        r=u2_closed, theta=categories_closed, fill='toself',
        name=u2.get('name') or u2['username'],
        line=dict(color='#10b981', width=2),
        fillcolor='rgba(16,185,129,0.15)',
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5], tickfont=dict(size=10))),
        showlegend=True,
        legend=dict(font=dict(size=11)),
        margin=dict(l=20, r=20, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        height=240,
    )
    return fig


def create_breakdown_bar(breakdown: dict, score: int) -> go.Figure:
    """Horizontal stacked bar showing score contribution by category."""
    if not breakdown:
        return None
    cats = list(breakdown.keys())
    vals = list(breakdown.values())
    colors = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4"]

    fig = go.Figure()
    for i, (cat, val) in enumerate(zip(cats, vals)):
        fig.add_trace(go.Bar(
            name=cat, x=[val], y=["Score"],
            orientation='h',
            marker_color=colors[i % len(colors)],
            text=f"{cat}: {val}pts",
            textposition='inside',
            insidetextanchor='middle',
            hovertemplate=f"{cat}: {val} pts<extra></extra>",
        ))
    fig.update_layout(
        barmode='stack',
        height=55,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


# ── ICS helpers ───────────────────────────────────────────────────────────────

def _next_weekday(day_name: str) -> date:
    """Returns the next calendar date for the given weekday name."""
    target = DAYS.index(day_name)
    today = date.today()
    days_ahead = (target - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


def _slot_hour(timeslot: str) -> int:
    return {TIMESLOTS[0]: 9, TIMESLOTS[1]: 13, TIMESLOTS[2]: 18}.get(timeslot, 9)


def generate_ics(group: dict) -> bytes:
    """Generate ICS with real dated events based on group meeting slots."""
    cal = Calendar()
    cal.add('prodid', '-//Study Group Matcher Pro//EN//')
    cal.add('version', '2.0')

    suggested = MatcherService.suggest_meeting_slots(group['id'])

    if suggested:
        for day, ts, count in suggested:
            next_date = _next_weekday(day)
            hour = _slot_hour(ts)
            event = Event()
            event.add('summary', f"📚 Study: {group['name']}")
            event.add('dtstart', datetime(next_date.year, next_date.month, next_date.day, hour, 0))
            event.add('dtend', datetime(next_date.year, next_date.month, next_date.day, hour + 2, 0))
            event.add('description',
                      f"Subject: {group['subject']}\nGoals: {group.get('goals', '')}\n"
                      f"{count} member(s) available this slot.")
            event.add('location', group.get('meeting_times') or 'TBD')
            cal.add_component(event)
    else:
        # Fallback: single event using meeting_times text
        event = Event()
        event.add('summary', f"📚 Study: {group['name']}")
        event.add('dtstart', datetime.now() + timedelta(days=1))
        event.add('dtend', datetime.now() + timedelta(days=1, hours=2))
        event.add('description',
                  f"Subject: {group['subject']}\nMeeting Times: {group.get('meeting_times', 'TBD')}")
        cal.add_component(event)

    return cal.to_ical()


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    user_id = st.session_state.user_id
    current_user = database.get_user_by_id(user_id)

    st.markdown(
        "<div class='page-header'><h2>Matches & Groups</h2>"
        "<p>Find compatible study partners and join or create groups.</p></div>",
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Find Matches", "⚖️ Weight Studio", "🌐 Browse Groups", "➕ Create Group"])

    # ── Tab 1: Find Matches ─────────────────────────────────────────────────
    with tab1:
        st.markdown("### Compatible Study Partners")

        filter_col1, filter_col2 = st.columns([2, 3])
        with filter_col1:
            min_score = st.slider("Minimum compatibility score", 0, 100, 20, step=5)
        with filter_col2:
            user_subjects = current_user.get('subjects') or []
            subject_filter = st.multiselect(
                "Filter by shared subject",
                options=user_subjects,
                placeholder="All shared subjects",
            )

        custom_weights = st.session_state.get('custom_weights')

        with st.spinner("Finding your best matches..."):
            all_matches = MatcherService.get_top_matches(user_id, custom_weights=custom_weights)

        filtered = [m for m in all_matches if m['score'] >= min_score]
        if subject_filter:
            filtered = [
                m for m in filtered
                if any(s in set(m['user'].get('subjects', [])) for s in subject_filter)
            ]

        if not current_user.get('subjects'):
            st.markdown("""
            <div style='text-align:center;padding:48px 20px;background:#f8fafc;border-radius:16px;border:1px dashed #cbd5e1;'>
                <div style='font-size:48px;'>🎯</div>
                <div style='font-size:18px;font-weight:700;color:#0f172a;margin:12px 0 6px;'>No subjects yet</div>
                <div style='color:#64748b;'>Add subjects to your profile to unlock match scoring.</div>
            </div>
            """, unsafe_allow_html=True)
        elif not filtered:
            st.markdown("""
            <div style='text-align:center;padding:48px 20px;background:#f8fafc;border-radius:16px;border:1px dashed #cbd5e1;'>
                <div style='font-size:48px;'>🔍</div>
                <div style='font-size:18px;font-weight:700;color:#0f172a;margin:12px 0 6px;'>No matches found</div>
                <div style='color:#64748b;'>Lower the score filter or adjust your subject filter.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.caption(f"Showing **{len(filtered)}** compatible peer(s)")
            for match in filtered:
                mu = match['user']
                score = match['score']
                col = score_color(score)
                lbl = score_label(score)
                shared_subs = list(
                    set(current_user.get('subjects', [])).intersection(set(mu.get('subjects', [])))
                )
                display_name = mu.get('name') or mu['username']
                course_info = mu.get('course') or "Course not set"
                uni_info = mu.get('university') or ""
                degree = mu.get('degree_level') or ""

                with st.container(border=True):
                    colA, colB, colC = st.columns([1, 3, 2])

                    with colA:
                        st.markdown(
                            f'<img src="{get_avatar_url(mu["username"])}" width="80" '
                            f'style="border-radius:50%;border:2px solid {col};display:block;margin:auto;">',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"<div style='text-align:center;margin-top:8px;"
                            f"color:{col};font-size:22px;font-weight:800;'>{score}%</div>"
                            f"<div style='text-align:center;color:{col};font-size:11px;"
                            f"font-weight:600;text-transform:uppercase;letter-spacing:0.8px;'>{lbl}</div>",
                            unsafe_allow_html=True,
                        )

                    with colB:
                        st.markdown(f"**{display_name}**")
                        meta = " · ".join(filter(None, [degree, course_info, uni_info]))
                        st.caption(meta or "Profile incomplete")

                        if mu.get('subjects'):
                            pills_html = "".join(
                                f"<span class='tag-pill {'blue' if s in shared_subs else ''}'>{s}</span>"
                                for s in mu['subjects']
                            )
                            st.markdown(f"<div style='margin:4px 0;'>{pills_html}</div>", unsafe_allow_html=True)

                        if match.get('details'):
                            st.markdown("**Why you match:**")
                            for detail in match['details']:
                                st.markdown(f"<span style='font-size:13px;'>• {detail}</span>",
                                            unsafe_allow_html=True)

                        # Score breakdown bar
                        if match.get('breakdown'):
                            bd_fig = create_breakdown_bar(match['breakdown'], score)
                            if bd_fig:
                                st.plotly_chart(bd_fig, use_container_width=True, key=f"bd_{mu['id']}")

                    with colC:
                        fig = create_radar_chart(current_user, mu, shared_subs)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, key=f"radar_{mu['id']}")
                        else:
                            st.markdown(
                                "<div style='padding:20px;text-align:center;color:#94a3b8;font-size:13px;'>"
                                "No shared subjects<br>for skill comparison</div>",
                                unsafe_allow_html=True,
                            )

                    # Full profile expander
                    with st.expander(f"👤 View {display_name}'s full profile"):
                        pc1, pc2 = st.columns([1, 3])
                        with pc1:
                            st.markdown(
                                f'<img src="{get_avatar_url(mu["username"])}" width="80" '
                                f'style="border-radius:50%;border:2px solid #e2e8f0;display:block;">',
                                unsafe_allow_html=True,
                            )
                        with pc2:
                            st.markdown(f"**{display_name}** &nbsp; `@{mu['username']}`")
                            info_line = " · ".join(filter(None, [degree, course_info, uni_info]))
                            if info_line:
                                st.caption(info_line)

                        if mu.get('subjects') and mu.get('skill_levels'):
                            st.markdown("**Subjects & Skill Levels**")
                            skill_html = "".join(
                                f"<span class='tag-pill {'blue' if s in shared_subs else ''}'>"
                                f"{s} {'⭐' * mu['skill_levels'].get(s, 3)}</span>"
                                for s in mu['subjects']
                            )
                            st.markdown(skill_html, unsafe_allow_html=True)

                        details_cols = st.columns(3)
                        with details_cols[0]:
                            if mu.get('goals'):
                                st.markdown("**Goals**")
                                for g in mu['goals']:
                                    st.markdown(f"<span class='tag-pill green'>{g}</span>",
                                                unsafe_allow_html=True)
                        with details_cols[1]:
                            if mu.get('study_styles'):
                                st.markdown("**Study Style**")
                                for s in mu['study_styles']:
                                    st.markdown(f"<span class='tag-pill purple'>{s}</span>",
                                                unsafe_allow_html=True)
                        with details_cols[2]:
                            if mu.get('study_vibe'):
                                st.markdown("**Vibe**")
                                for v in mu['study_vibe']:
                                    st.markdown(f"<span class='tag-pill'>{v}</span>",
                                                unsafe_allow_html=True)

                        if mu.get('location_zone'):
                            st.caption(f"📍 {mu['location_zone']}")
                        if mu.get('study_environment'):
                            env_str = " · ".join(mu['study_environment'])
                            st.caption(f"🏛️ Prefers: {env_str}")

                    st.caption("💬 Connect via your shared group workspace")

    # ── Tab 2: Match Weight Studio ──────────────────────────────────────────
    with tab2:
        st.markdown("### ⚖️ Match Weight Studio")
        st.markdown(
            "<p style='color:#64748b;'>Adjust how much each factor matters to you. "
            "Scores update live when you return to the Matches tab.</p>",
            unsafe_allow_html=True,
        )

        SCORE_CATEGORIES = [
            ("Subjects", "📚 Shared Subjects"),
            ("Schedule", "📅 Schedule Overlap"),
            ("Study Style", "🧠 Study Style"),
            ("Goals", "🎯 Goals"),
            ("Skill Match", "⚡ Skill Compatibility"),
            ("Location & Context", "📍 Location & Course"),
            ("Vibe & Environment", "🌿 Vibe & Environment"),
            ("Degree Level", "🎓 Degree Level"),
        ]

        existing = st.session_state.get('custom_weights', {})
        new_weights = {}

        col1, col2 = st.columns(2)
        for i, (key, label) in enumerate(SCORE_CATEGORIES):
            with (col1 if i % 2 == 0 else col2):
                val = st.slider(
                    label,
                    min_value=0.0, max_value=2.0,
                    value=float(existing.get(key, 1.0)),
                    step=0.1,
                    key=f"weight_{key}",
                    help="1.0 = default weight · 0 = ignore · 2.0 = double importance",
                )
                new_weights[key] = val

        col_apply, col_reset = st.columns([1, 1])
        with col_apply:
            if st.button("Apply Weights", type="primary", use_container_width=True):
                st.session_state['custom_weights'] = new_weights
                cache_key = f"matches_{user_id}"
                if cache_key in st.session_state:
                    del st.session_state[cache_key]
                st.toast("Weights applied! Go to Find Matches to see updated scores.", icon="⚖️")
        with col_reset:
            if st.button("Reset to Defaults", use_container_width=True):
                st.session_state.pop('custom_weights', None)
                cache_key = f"matches_{user_id}"
                if cache_key in st.session_state:
                    del st.session_state[cache_key]
                st.toast("Weights reset to defaults.", icon="↩️")
                st.rerun()

        st.markdown("---")
        st.markdown(
            "<div style='background:#f0f9ff;border-radius:12px;padding:16px;border:1px solid #bae6fd;'>"
            "<strong>How it works:</strong> The matcher scores each dimension independently. "
            "Setting a weight to <strong>2.0</strong> doubles its contribution; "
            "<strong>0</strong> removes it entirely. This lets you find peers optimised for your situation — "
            "e.g., maximise schedule overlap if you need someone to study with this week."
            "</div>",
            unsafe_allow_html=True,
        )

    # ── Tab 3: Browse Groups ────────────────────────────────────────────────
    with tab3:
        st.markdown("### Public Study Groups")

        all_groups = database.get_all_groups()
        user_groups = database.get_user_groups(user_id)
        user_group_ids = {g['id'] for g in user_groups}

        # Filter bar
        filter_col, _ = st.columns([2, 3])
        with filter_col:
            group_subject_filter = st.selectbox(
                "Filter by subject", ["All subjects"] + AVAILABLE_SUBJECTS, index=0
            )

        if group_subject_filter != "All subjects":
            all_groups = [g for g in all_groups if g.get('subject') == group_subject_filter]

        if not all_groups:
            st.markdown("""
            <div style='text-align:center;padding:48px 20px;background:#f8fafc;border-radius:16px;border:1px dashed #cbd5e1;'>
                <div style='font-size:48px;'>🌐</div>
                <div style='font-size:18px;font-weight:700;color:#0f172a;margin:12px 0 6px;'>No groups found</div>
                <div style='color:#64748b;'>Be the first to create a group in this subject!</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for group in all_groups:
                is_member = group['id'] in user_group_ids
                member_count = len(group['members'])
                max_members = group.get('max_members', 8)
                is_full = member_count >= max_members
                member_names = group.get('member_names') or []

                # Compute group fit score for non-members
                fit_avg, fit_min = (0, 0)
                if not is_member and member_count > 0:
                    fit_avg, fit_min = MatcherService.calculate_group_fit(user_id, group['id'])

                with st.container(border=True):
                    colA, colB = st.columns([4, 1])
                    with colA:
                        header_parts = [f"**{group['name']}**"]
                        if not is_member and fit_avg > 0:
                            fc = score_color(fit_avg)
                            header_parts.append(
                                f"&nbsp;<span style='color:{fc};font-size:13px;font-weight:700;'>"
                                f"Fit: {fit_avg}%</span>"
                            )
                        st.markdown(" ".join(header_parts), unsafe_allow_html=True)

                        cols_meta = st.columns(4)
                        with cols_meta[0]:
                            st.markdown(f"<span class='tag-pill blue'>📚 {group['subject']}</span>",
                                        unsafe_allow_html=True)
                        with cols_meta[1]:
                            st.markdown(f"<span class='tag-pill'>⏰ {group['meeting_times'] or 'TBD'}</span>",
                                        unsafe_allow_html=True)
                        with cols_meta[2]:
                            capacity_color = "green" if not is_full else "amber"
                            st.markdown(
                                f"<span class='tag-pill {capacity_color}'>👥 {member_count}/{max_members}</span>",
                                unsafe_allow_html=True,
                            )
                        with cols_meta[3]:
                            if is_full:
                                st.markdown("<span class='tag-pill amber'>🔒 Full</span>",
                                            unsafe_allow_html=True)

                        if member_names:
                            st.caption("Members: " + ", ".join(member_names))
                        if group.get('goals'):
                            st.markdown(f"<span style='font-size:13px;color:#64748b;'>{group['goals']}</span>",
                                        unsafe_allow_html=True)

                    with colB:
                        if is_member:
                            st.success("Joined ✅")
                            ics_data = generate_ics(group)
                            st.download_button(
                                label="📆 Export ICS",
                                data=ics_data,
                                file_name=f"{group['name'].replace(' ', '_')}.ics",
                                mime="text/calendar",
                                key=f"dl_{group['id']}",
                                use_container_width=True,
                            )
                            confirm_key = f"confirm_leave_{group['id']}"
                            if not st.session_state.get(confirm_key):
                                if st.button("Leave", key=f"leave_{group['id']}", use_container_width=True):
                                    st.session_state[confirm_key] = True
                                    st.rerun()
                            else:
                                st.warning("Leave this group?")
                                if st.button("Yes, leave", key=f"confirm_yes_{group['id']}",
                                             type="primary", use_container_width=True):
                                    database.leave_group(group['id'], user_id)
                                    database.log_activity(user_id, 'left_group', {'group': group['name']})
                                    cache_key = f"matches_{user_id}"
                                    st.session_state.pop(cache_key, None)
                                    st.session_state.pop(confirm_key, None)
                                    st.toast("Left group.", icon="👋")
                                    st.rerun()
                                if st.button("Cancel", key=f"cancel_leave_{group['id']}",
                                             use_container_width=True):
                                    st.session_state.pop(confirm_key, None)
                                    st.rerun()
                        else:
                            if is_full:
                                st.button("Group Full", disabled=True, use_container_width=True)
                            else:
                                if st.button("Join Group", key=f"join_{group['id']}",
                                             type="primary", use_container_width=True):
                                    database.join_group(group['id'], user_id)
                                    database.log_activity(user_id, 'joined_group', {'group': group['name']})
                                    cache_key = f"matches_{user_id}"
                                    st.session_state.pop(cache_key, None)
                                    st.toast(f"Joined {group['name']}!", icon="🎉")
                                    st.rerun()

    # ── Tab 4: Create Group ─────────────────────────────────────────────────
    with tab4:
        st.markdown("### Create a New Study Group")
        with st.form("create_group_form"):
            g_name = st.text_input("Group Name *", placeholder="e.g. Linear Algebra Warriors")
            col1, col2 = st.columns(2)
            with col1:
                g_subject = st.selectbox("Subject Focus *", options=AVAILABLE_SUBJECTS)
                g_max = st.number_input("Max Members", min_value=2, max_value=20, value=8)
            with col2:
                g_times = st.text_input("Meeting Times *", placeholder="e.g. Mon/Wed 6pm, Online")
                g_private = st.checkbox("Private group (invite only)")
            g_goals = st.text_area(
                "Group Goals & Topics",
                placeholder="e.g. Cover chapters 1-5 before the midterm, weekly problem sets...",
                height=80,
            )
            g_desc = st.text_area(
                "Description (optional)",
                placeholder="Tell potential members more about this group...",
                height=60,
            )
            submitted = st.form_submit_button("Create Group", type="primary", use_container_width=True)

            if submitted:
                if g_name.strip() and g_times.strip():
                    gid = database.create_group(
                        g_name.strip(), g_subject, g_times.strip(), g_goals, user_id
                    )
                    if gid != -1:
                        database.log_activity(user_id, 'created_group', {'group': g_name.strip()})
                        st.toast(f"Group '{g_name}' created!", icon="✅")
                        st.rerun()
                    else:
                        st.error("Could not create the group. Please try again.")
                else:
                    st.error("Group Name and Meeting Times are required.")
