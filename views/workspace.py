import streamlit as st
import database
from matcher import MatcherService
import plotly.graph_objects as go
from datetime import datetime, date
from config import KANBAN_STATUSES, KANBAN_PRIORITIES, DAYS, TIMESLOTS, SLOT_ICONS
from utils import priority_color, priority_icon

PRIORITY_ORDER = {p: i for i, p in enumerate(["High", "Medium", "Low"])}


def _sort_tasks(tasks: list) -> list:
    def sort_key(t):
        p = PRIORITY_ORDER.get(t.get('priority', 'Medium'), 1)
        due = t.get('due_date') or "9999-12-31"
        return (p, due)
    return sorted(tasks, key=sort_key)


def _render_cohesion_heatmap(group_id: int):
    data = MatcherService.calculate_group_cohesion(group_id)
    names = data['names']
    matrix = data['matrix']
    avg = data['avg']

    if not names or len(names) < 2:
        st.info("Need at least 2 members to show group cohesion.")
        return

    col_score, _ = st.columns([1, 3])
    with col_score:
        color = "#10b981" if avg >= 60 else ("#f59e0b" if avg >= 35 else "#ef4444")
        st.markdown(
            f"<div style='background:white;border-radius:12px;padding:16px;text-align:center;"
            f"border-top:4px solid {color};box-shadow:0 2px 8px rgba(0,0,0,0.05);'>"
            f"<div style='color:#94a3b8;font-size:11px;text-transform:uppercase;letter-spacing:1.2px;"
            f"font-weight:600;'>Group Cohesion</div>"
            f"<div style='color:{color};font-size:36px;font-weight:800;'>{avg}%</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=names,
        y=names,
        colorscale=[[0, "#fef2f2"], [0.4, "#fef3c7"], [0.7, "#d1fae5"], [1.0, "#059669"]],
        zmin=0, zmax=100,
        text=[[f"{v}%" for v in row] for row in matrix],
        texttemplate="%{text}",
        textfont=dict(size=12, color="white"),
        hovertemplate="%{y} × %{x}: %{z}%<extra></extra>",
        showscale=True,
        colorbar=dict(title="Compat %", thickness=12, len=0.8),
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=max(250, len(names) * 60),
        xaxis=dict(side='bottom'),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Each cell shows the pairwise compatibility score between two members. "
        "Diagonal is always 100%. Darker green = stronger connection."
    )


def _render_session_planner(group: dict):
    st.markdown("### 📆 Optimal Session Planner")
    st.markdown(
        "<p style='color:#64748b;'>Based on group member availability and open task priority.</p>",
        unsafe_allow_html=True,
    )

    slots = MatcherService.suggest_meeting_slots(group['id'])
    total = len(group['members'])

    if not slots:
        st.info("No availability data yet. Ask group members to set their schedules in the Availability tab.")
        return

    tasks = database.get_group_tasks(group['id'])
    open_tasks = _sort_tasks([t for t in tasks if t['status'] != 'Done'])
    top_task = open_tasks[0] if open_tasks else None

    for i, (day, ts, count) in enumerate(slots):
        pct = int(count / total * 100) if total > 0 else 0
        icon = SLOT_ICONS[TIMESLOTS.index(ts)] if ts in TIMESLOTS else "📅"
        bar_color = "#10b981" if pct >= 75 else ("#f59e0b" if pct >= 50 else "#94a3b8")
        rank_label = ["🥇 Best slot", "🥈 Second best", "🥉 Third best"][i]

        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                st.markdown(
                    f"<div style='font-weight:700;font-size:15px;'>{icon} {day} · {ts.split('(')[0].strip()}</div>"
                    f"<div style='color:#64748b;font-size:13px;margin-top:2px;'>{rank_label}</div>",
                    unsafe_allow_html=True,
                )
                if top_task:
                    pcol = priority_color(top_task.get('priority', 'Medium'))
                    st.markdown(
                        f"<div style='margin-top:6px;font-size:12px;color:#64748b;'>"
                        f"Suggested task: <span style='color:{pcol};font-weight:600;'>"
                        f"{priority_icon(top_task.get('priority','Medium'))} {top_task['title']}</span></div>",
                        unsafe_allow_html=True,
                    )
            with c2:
                st.markdown(
                    f"<div style='margin-top:4px;'>"
                    f"<div style='font-size:13px;color:#64748b;margin-bottom:4px;'>"
                    f"{count}/{total} members free ({pct}%)</div>"
                    f"<div style='height:8px;border-radius:999px;background:#e2e8f0;overflow:hidden;'>"
                    f"<div style='height:100%;width:{pct}%;background:{bar_color};border-radius:999px;'></div>"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )
            with c3:
                from views.matches import generate_ics, _next_weekday, _slot_hour
                from datetime import datetime, timedelta, date as _date
                from icalendar import Calendar, Event as ICSEvent

                # Build single-slot ICS
                cal = Calendar()
                cal.add('prodid', '-//Study Group Matcher Pro//EN//')
                cal.add('version', '2.0')
                next_date = _next_weekday(day)
                hour = _slot_hour(ts)
                ev = ICSEvent()
                ev.add('summary', f"📚 Study: {group['name']}")
                ev.add('dtstart', datetime(next_date.year, next_date.month, next_date.day, hour, 0))
                ev.add('dtend', datetime(next_date.year, next_date.month, next_date.day, hour + 2, 0))
                ev.add('description',
                       f"Subject: {group['subject']}\n"
                       + (f"Task: {top_task['title']}" if top_task else ""))
                cal.add_component(ev)

                st.download_button(
                    "📥 ICS",
                    data=cal.to_ical(),
                    file_name=f"{group['name'].replace(' ','_')}_{day}.ics",
                    mime="text/calendar",
                    key=f"slot_ics_{group['id']}_{i}",
                    use_container_width=True,
                )


def render():
    user_id = st.session_state.user_id
    user_groups = database.get_user_groups(user_id)

    st.markdown(
        "<div class='page-header'><h2>Group Workspaces</h2>"
        "<p>Manage tasks, track cohesion, and plan sessions with your study groups.</p></div>",
        unsafe_allow_html=True,
    )

    if not user_groups:
        st.markdown("""
        <div style='text-align:center;padding:60px 20px;background:#f8fafc;border-radius:16px;border:1px dashed #cbd5e1;'>
            <div style='font-size:48px;'>🛠️</div>
            <div style='font-size:18px;font-weight:700;color:#0f172a;margin:12px 0 6px;'>No workspaces yet</div>
            <div style='color:#64748b;'>Join or create a study group to unlock your team workspace.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    group_options = {g['name']: g for g in user_groups}
    selected_group_name = st.selectbox("Select Workspace", options=list(group_options.keys()))

    if not selected_group_name:
        return

    group = group_options[selected_group_name]

    # Group info strip
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.markdown(f"<span class='tag-pill blue'>📚 {group['subject']}</span>", unsafe_allow_html=True)
    with col_info2:
        meeting = group.get('meeting_times') or 'TBD'
        st.markdown(f"<span class='tag-pill'>⏰ {meeting}</span>", unsafe_allow_html=True)
    with col_info3:
        max_m = group.get('max_members', 8)
        st.markdown(f"<span class='tag-pill green'>👥 {len(group['members'])}/{max_m} members</span>",
                    unsafe_allow_html=True)

    if group.get('goals'):
        st.caption(f"Goals: {group['goals']}")

    st.markdown("---")

    ws_tab1, ws_tab2, ws_tab3 = st.tabs(["📋 Kanban Board", "📊 Group Dynamics", "📆 Session Planner"])

    # ── Kanban Board ──────────────────────────────────────────────────────────
    with ws_tab1:
        # Add task form
        with st.expander("➕ Add New Task", expanded=False):
            with st.form("new_task_form", clear_on_submit=True):
                new_task = st.text_input("Task title *", placeholder="e.g. Finish problem set 3")
                fc1, fc2, fc3 = st.columns(3)
                with fc1:
                    task_priority = st.selectbox("Priority", KANBAN_PRIORITIES,
                                                 index=1, key="new_task_priority")
                with fc2:
                    task_due = st.date_input("Due date (optional)", value=None, key="new_task_due")
                with fc3:
                    members = database.get_group_member_names(group['id'])
                    member_options = {m['name']: m['id'] for m in members}
                    assignee_name = st.selectbox(
                        "Assign to", ["Unassigned"] + list(member_options.keys()), key="new_task_assignee"
                    )

                add_clicked = st.form_submit_button("Add Task", type="primary", use_container_width=True)
                if add_clicked:
                    if new_task.strip():
                        due_dt = datetime(task_due.year, task_due.month, task_due.day) if task_due else None
                        assigned_id = member_options.get(assignee_name) if assignee_name != "Unassigned" else None
                        database.add_group_task(
                            group['id'], new_task.strip(),
                            priority=task_priority,
                            due_date=due_dt,
                            assigned_to=assigned_id,
                        )
                        st.rerun()
                    else:
                        st.warning("Task title cannot be empty.")

        # Kanban columns
        tasks = database.get_group_tasks(group['id'])
        todo    = _sort_tasks([t for t in tasks if t['status'] == 'To Do'])
        in_prog = _sort_tasks([t for t in tasks if t['status'] == 'In Progress'])
        done    = [t for t in tasks if t['status'] == 'Done']

        col_todo, col_prog, col_done = st.columns(3)

        def _task_card_meta(t: dict) -> str:
            parts = []
            pc = priority_color(t.get('priority', 'Medium'))
            pi = priority_icon(t.get('priority', 'Medium'))
            parts.append(
                f"<span style='font-size:11px;font-weight:600;color:{pc};'>{pi} {t.get('priority','Medium')}</span>"
            )
            if t.get('due_date'):
                try:
                    due = datetime.fromisoformat(t['due_date'])
                    overdue = due < datetime.now()
                    dc = "#ef4444" if overdue else "#64748b"
                    label = "Overdue" if overdue else due.strftime("%b %d")
                    parts.append(f"<span style='font-size:11px;color:{dc};'>📅 {label}</span>")
                except Exception:
                    pass
            if t.get('assignee_name'):
                parts.append(f"<span style='font-size:11px;color:#64748b;'>👤 {t['assignee_name']}</span>")
            return " &nbsp;·&nbsp; ".join(parts)

        with col_todo:
            st.markdown(
                f"<div class='kanban-header'><span>📋 To Do</span>"
                f"<span class='kanban-count blue'>{len(todo)}</span></div>",
                unsafe_allow_html=True,
            )
            for t in todo:
                with st.container(border=True):
                    st.markdown(f"<span style='font-size:14px;font-weight:500;'>{t['title']}</span>",
                                unsafe_allow_html=True)
                    st.markdown(_task_card_meta(t), unsafe_allow_html=True)
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("▶ Start", key=f"start_{t['id']}", use_container_width=True,
                                     type="primary"):
                            database.update_task_status(t['id'], 'In Progress')
                            st.rerun()
                    with b2:
                        confirm_key = f"del_todo_{t['id']}"
                        if not st.session_state.get(confirm_key):
                            if st.button("🗑", key=f"del_btn_todo_{t['id']}", use_container_width=True):
                                st.session_state[confirm_key] = True
                                st.rerun()
                        else:
                            if st.button("Confirm delete", key=f"del_confirm_todo_{t['id']}",
                                         use_container_width=True, type="primary"):
                                database.delete_task(t['id'])
                                st.session_state.pop(confirm_key, None)
                                st.rerun()

        with col_prog:
            st.markdown(
                f"<div class='kanban-header'><span>⚡ In Progress</span>"
                f"<span class='kanban-count amber'>{len(in_prog)}</span></div>",
                unsafe_allow_html=True,
            )
            for t in in_prog:
                with st.container(border=True):
                    st.markdown(f"<span style='font-size:14px;font-weight:500;'>{t['title']}</span>",
                                unsafe_allow_html=True)
                    st.markdown(_task_card_meta(t), unsafe_allow_html=True)
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("✅ Done", key=f"done_{t['id']}", use_container_width=True,
                                     type="primary"):
                            database.update_task_status(t['id'], 'Done')
                            database.log_activity(user_id, 'task_completed', {'task': t['title']})
                            st.rerun()
                    with b2:
                        confirm_key = f"del_prog_{t['id']}"
                        if not st.session_state.get(confirm_key):
                            if st.button("🗑", key=f"del_btn_prog_{t['id']}", use_container_width=True):
                                st.session_state[confirm_key] = True
                                st.rerun()
                        else:
                            if st.button("Confirm delete", key=f"del_confirm_prog_{t['id']}",
                                         use_container_width=True, type="primary"):
                                database.delete_task(t['id'])
                                st.session_state.pop(confirm_key, None)
                                st.rerun()

        with col_done:
            st.markdown(
                f"<div class='kanban-header'><span>✅ Completed</span>"
                f"<span class='kanban-count green'>{len(done)}</span></div>",
                unsafe_allow_html=True,
            )
            for t in done:
                with st.container(border=True):
                    st.markdown(
                        f"<span style='font-size:14px;color:#94a3b8;text-decoration:line-through;'>"
                        f"{t['title']}</span>",
                        unsafe_allow_html=True,
                    )
                    confirm_key = f"del_done_{t['id']}"
                    if not st.session_state.get(confirm_key):
                        if st.button("🗑 Remove", key=f"del_btn_done_{t['id']}", use_container_width=True):
                            st.session_state[confirm_key] = True
                            st.rerun()
                    else:
                        if st.button("Confirm remove", key=f"del_confirm_done_{t['id']}",
                                     use_container_width=True, type="primary"):
                            database.delete_task(t['id'])
                            st.session_state.pop(confirm_key, None)
                            st.rerun()

        if not tasks:
            st.markdown(
                "<div style='text-align:center;padding:40px;color:#94a3b8;'>"
                "No tasks yet — expand 'Add New Task' above to get started!</div>",
                unsafe_allow_html=True,
            )

    # ── Group Dynamics (Cohesion Heatmap) ────────────────────────────────────
    with ws_tab2:
        st.markdown("### 📊 Group Dynamics")
        st.markdown(
            "<p style='color:#64748b;'>Pairwise compatibility scores between all group members. "
            "Reveals natural study pairs and potential friction points.</p>",
            unsafe_allow_html=True,
        )
        _render_cohesion_heatmap(group['id'])

    # ── Session Planner ────────────────────────────────────────────────────────
    with ws_tab3:
        _render_session_planner(group)
