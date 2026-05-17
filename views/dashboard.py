import streamlit as st
import database
from matcher import MatcherService
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from config import DAYS, TIMESLOTS
from utils import score_color, score_label, calculate_profile_completion


# ── Platform-wide analytics ───────────────────────────────────────────────────

def _render_platform_analytics():
    """Aggregated, anonymised platform insights — Outstanding Feature 3."""
    from config import AVAILABLE_SUBJECTS

    all_users = database.get_all_users()
    all_avail = database.get_all_availability()
    all_groups = database.get_all_groups()
    total_users = len(all_users)

    if total_users < 3:
        return

    with st.expander("🌐 Platform Insights", expanded=False):
        st.markdown(
            "<p style='color:#64748b;font-size:13px;'>Anonymised, aggregated data across "
            f"all {total_users} platform members.</p>",
            unsafe_allow_html=True,
        )
        col_a, col_b = st.columns(2)

        # Subject popularity bar chart
        with col_a:
            st.markdown("**Most studied subjects**")
            subject_counts: dict = {}
            for u in all_users:
                for subj in u.get('subjects', []):
                    subject_counts[subj] = subject_counts.get(subj, 0) + 1
            if subject_counts:
                top = sorted(subject_counts.items(), key=lambda x: x[1], reverse=True)[:8]
                names_s = [t[0] for t in top]
                vals_s = [t[1] for t in top]
                fig_bar = go.Figure(go.Bar(
                    x=vals_s, y=names_s, orientation='h',
                    marker_color='#4f46e5',
                    text=vals_s, textposition='outside',
                ))
                fig_bar.update_layout(
                    height=260,
                    margin=dict(l=0, r=30, t=0, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(visible=False),
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        # Platform availability heatmap — "prime time"
        with col_b:
            st.markdown("**Platform prime time** (% of users free)")
            if all_avail:
                slot_matrix = [[0] * len(DAYS) for _ in TIMESLOTS]
                for uid, slots in all_avail.items():
                    for day, ts in slots:
                        if day in DAYS and ts in TIMESLOTS:
                            slot_matrix[TIMESLOTS.index(ts)][DAYS.index(day)] += 1
                pct_matrix = [
                    [round(v / total_users * 100) for v in row]
                    for row in slot_matrix
                ]
                fig_heat = go.Figure(go.Heatmap(
                    z=pct_matrix,
                    x=[d[:3] for d in DAYS],
                    y=["Morn.", "Aftn.", "Eve."],
                    colorscale=[[0, "#f1f5f9"], [1, "#4f46e5"]],
                    showscale=False,
                    text=[[f"{v}%" for v in row] for row in pct_matrix],
                    texttemplate="%{text}",
                    textfont=dict(size=11),
                    xgap=3, ygap=3,
                ))
                fig_heat.update_layout(
                    height=140,
                    margin=dict(l=0, r=0, t=0, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_heat, use_container_width=True)

        # Quick stats row
        active_groups = len([g for g in all_groups if len(g['members']) > 0])
        subjects_without_groups = [
            s for s in AVAILABLE_SUBJECTS
            if not any(g['subject'] == s for g in all_groups)
            and subject_counts.get(s, 0) > 1
        ]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Active Groups", active_groups)
        with c2:
            st.metric("Total Members", total_users)
        with c3:
            st.metric("Subjects Studied", len(subject_counts))

        if subjects_without_groups:
            gap = subjects_without_groups[0]
            st.info(
                f"💡 **Group gap:** {len(subject_counts.get(gap, 0))} or more students study "
                f"**{gap}** but there are no groups yet — be the first to create one!"
            )


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    user_id = st.session_state.user_id
    user = database.get_user_by_id(user_id)
    display_name = user.get('name') or user['username']

    st.markdown(
        f"<div class='page-header'>"
        f"<h2>Welcome back, {display_name} 👋</h2>"
        f"<p>Your study overview and analytics at a glance.</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── Compute data ─────────────────────────────────────────────────────────
    user_groups  = database.get_user_groups(user_id)
    availability = database.get_user_availability(user_id)
    completion   = calculate_profile_completion(user)
    with st.spinner("Loading your matches…"):
        top_matches = MatcherService.get_top_matches(user_id)
    best_score = top_matches[0]['score'] if top_matches else 0

    # ── Summary Metric Cards ─────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"<div class='metric-card'><h4>Active Groups</h4><h2>{len(user_groups)}</h2></div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"<div class='metric-card green'><h4>Compatible Peers</h4><h2>{len(top_matches)}</h2></div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"<div class='metric-card amber'><h4>Best Match</h4><h2>{best_score}%</h2></div>",
            unsafe_allow_html=True,
        )
    with col4:
        color_cls = "green" if completion == 100 else ("amber" if completion >= 50 else "")
        st.markdown(
            f"<div class='metric-card {color_cls}'><h4>Profile Complete</h4><h2>{completion}%</h2>"
            f"<div class='profile-progress-bar'><div class='profile-progress-fill' "
            f"style='width:{completion}%'></div></div></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Main content row ──────────────────────────────────────────────────────
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("<div class='section-title'>Study Distribution</div>", unsafe_allow_html=True)

        if user.get('subjects') and user.get('skill_levels'):
            subjects = user['subjects']
            skill_levels = user.get('skill_levels', {})
            skill_vals = [skill_levels.get(s, 3) for s in subjects]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=subjects,
                y=skill_vals,
                marker=dict(
                    color=skill_vals,
                    colorscale='Blues',
                    cmin=1, cmax=5,
                    line=dict(color='white', width=1),
                ),
                text=[f"Level {v}" for v in skill_vals],
                textposition='outside',
            ))
            fig.update_layout(
                yaxis=dict(range=[0, 5.8], title="Skill Level (1–5)", tickmode='linear', dtick=1),
                xaxis_title=None,
                margin=dict(t=20, b=10, l=0, r=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                height=260,
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
            st.plotly_chart(fig, use_container_width=True)
        elif user.get('subjects'):
            df = pd.DataFrame({"Subject": user['subjects'], "Weight": [1] * len(user['subjects'])})
            fig = px.pie(df, values='Weight', names='Subject', hole=0.45,
                         color_discrete_sequence=px.colors.sequential.Blues_r)
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0),
                              paper_bgcolor="rgba(0,0,0,0)", height=260)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("""
            <div style='text-align:center;padding:40px 20px;background:#f8fafc;border-radius:16px;border:1px dashed #cbd5e1;'>
                <div style='font-size:40px;'>📊</div>
                <div style='font-size:16px;font-weight:700;color:#0f172a;margin:10px 0 4px;'>No skill data yet</div>
                <div style='color:#64748b;font-size:14px;'>Add subjects in My Profile to see your analytics.</div>
            </div>
            """, unsafe_allow_html=True)

        # Availability heatmap
        if availability:
            st.markdown("<div class='section-title' style='margin-top:20px;'>Weekly Availability</div>",
                        unsafe_allow_html=True)
            avail_set = set(availability)
            matrix = [[1 if (d, s) in avail_set else 0 for d in DAYS] for s in TIMESLOTS]
            fig2 = go.Figure(go.Heatmap(
                z=matrix,
                x=[d[:3] for d in DAYS],
                y=["Morn.", "Aftn.", "Eve."],
                colorscale=[[0, "#f1f5f9"], [1, "#3b82f6"]],
                showscale=False,
                xgap=3, ygap=3,
            ))
            fig2.update_layout(
                margin=dict(t=10, b=10, l=0, r=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=110,
            )
            st.plotly_chart(fig2, use_container_width=True)

    with col_right:
        # Activity Feed
        st.markdown("<div class='section-title'>Recent Activity</div>", unsafe_allow_html=True)
        EVENT_ICONS = {
            'profile_saved':      ("✏️", lambda p: "Updated your profile"),
            'joined_group':       ("📚", lambda p: f"Joined group <b>{p.get('group','')}</b>"),
            'left_group':         ("👋", lambda p: f"Left group <b>{p.get('group','')}</b>"),
            'created_group':      ("🎉", lambda p: f"Created group <b>{p.get('group','')}</b>"),
            'task_completed':     ("✅", lambda p: f"Completed task: <b>{p.get('task','')}</b>"),
            'availability_saved': ("📅", lambda p: "Updated availability"),
        }
        real_events = database.get_recent_activity(user_id, limit=8)
        activities = []
        for ev in real_events:
            icon, fmt = EVENT_ICONS.get(ev['event_type'], ("📌", lambda p: ev['event_type']))
            activities.append((icon, fmt(ev['payload'])))

        if not real_events:
            if user_groups:
                for g in user_groups[:2]:
                    activities.append(("📚", f"Member of <b>{g['name']}</b> &nbsp;<span class='tag-pill blue'>{g['subject']}</span>"))
            if availability:
                activities.append(("📅", f"<b>{len(availability)}</b> availability slot(s) set"))
            if top_matches:
                best = top_matches[0]
                best_name = best['user'].get('name') or best['user']['username']
                bc = score_color(best['score'])
                activities.append(("🤝", f"Best match: <b>{best_name}</b> &nbsp;<span style='color:{bc};font-weight:700;'>{best['score']}%</span>"))
            if completion < 60:
                activities.append(("✏️", "Complete your profile to unlock better matches"))
            if not activities:
                activities.append(("👋", "Welcome! Complete your profile to get started."))

        for icon, text in activities:
            st.markdown(
                f"<div class='activity-item'><span style='font-size:18px;'>{icon}</span>"
                f"<span>{text}</span></div>",
                unsafe_allow_html=True,
            )

        # Top Matches Preview
        if top_matches:
            st.markdown("<div class='section-title' style='margin-top:20px;'>Top Matches</div>",
                        unsafe_allow_html=True)
            for m in top_matches[:3]:
                mu = m['user']
                sc = m['score']
                col = score_color(sc)
                lbl = score_label(sc)
                name = mu.get('name') or mu['username']
                course = mu.get('course') or "N/A"
                with st.container(border=True):
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown(f"**{name}**")
                        st.caption(course)
                    with cols[1]:
                        st.markdown(
                            f"<div style='text-align:center;'>"
                            f"<div style='color:{col};font-size:22px;font-weight:800;'>{sc}%</div>"
                            f"<div style='color:{col};font-size:11px;font-weight:600;'>{lbl}</div>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )

        # Profile completion nudge
        if completion < 100:
            st.markdown("<br>", unsafe_allow_html=True)
            missing = []
            if not user.get('name'): missing.append("Full Name")
            if not user.get('course'): missing.append("Course")
            if not user.get('degree_level'): missing.append("Degree Level")
            if not user.get('university'): missing.append("University")
            if not user.get('subjects'): missing.append("Subjects")
            if not user.get('goals'): missing.append("Goals")
            if missing:
                st.warning(f"**Boost your profile:** Add {', '.join(missing[:3])} to improve your matches.")

    # ── Platform Analytics (Outstanding Feature 3) ────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    _render_platform_analytics()
