import streamlit as st
import database
from matcher import MatcherService
from config import DAYS, TIMESLOTS, SLOT_ICONS

WEEKDAYS = DAYS[:5]


def _apply_preset(preset: str, avail_set: set) -> set:
    if preset == "weekday_mornings":
        return {(d, TIMESLOTS[0]) for d in WEEKDAYS}
    if preset == "weekday_evenings":
        return {(d, TIMESLOTS[2]) for d in WEEKDAYS}
    if preset == "all_weekdays":
        return {(d, ts) for d in WEEKDAYS for ts in TIMESLOTS}
    if preset == "clear":
        return set()
    return avail_set


def render():
    st.markdown(
        "<div class='page-header'><h2>Weekly Availability</h2>"
        "<p>Mark when you're free so peers and groups can sync with you.</p></div>",
        unsafe_allow_html=True,
    )

    user_id = st.session_state.user_id
    existing_avail = database.get_user_availability(user_id)

    # Apply any preset that was chosen outside the form
    preset = st.session_state.pop('avail_preset', None)
    if preset is not None:
        avail_set = _apply_preset(preset, set(existing_avail))
    else:
        avail_set = set(existing_avail)

    # ── Quick-fill buttons (outside form so they can trigger reruns) ──────────
    st.markdown("**Quick-fill:**")
    qc1, qc2, qc3, qc4 = st.columns(4)
    with qc1:
        if st.button("🌅 Weekday Mornings", use_container_width=True):
            st.session_state['avail_preset'] = 'weekday_mornings'
            st.rerun()
    with qc2:
        if st.button("🌙 Weekday Evenings", use_container_width=True):
            st.session_state['avail_preset'] = 'weekday_evenings'
            st.rerun()
    with qc3:
        if st.button("📅 All Weekdays", use_container_width=True):
            st.session_state['avail_preset'] = 'all_weekdays'
            st.rerun()
    with qc4:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state['avail_preset'] = 'clear'
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Availability grid form ────────────────────────────────────────────────
    with st.form("availability_form", border=True):
        header_cols = st.columns([2] + [1] * len(TIMESLOTS))
        with header_cols[0]:
            st.markdown("**Day**")
        for i, (ts, icon) in enumerate(zip(TIMESLOTS, SLOT_ICONS)):
            with header_cols[i + 1]:
                label = ts.split(' ')[0]
                st.markdown(f"**{icon} {label}**")

        st.markdown("<hr style='margin:8px 0;border-color:#f1f5f9;'>", unsafe_allow_html=True)

        new_selection = []
        for day in DAYS:
            row_cols = st.columns([2] + [1] * len(TIMESLOTS))
            with row_cols[0]:
                is_weekend = day in ["Saturday", "Sunday"]
                day_style = "color:#94a3b8;" if is_weekend else ""
                st.markdown(
                    f"<span style='font-size:14px;font-weight:500;{day_style}'>{day}</span>",
                    unsafe_allow_html=True,
                )
            for i, ts in enumerate(TIMESLOTS):
                with row_cols[i + 1]:
                    checked = st.checkbox(
                        "Free",
                        value=(day, ts) in avail_set,
                        key=f"{day}_{ts}",
                        label_visibility="collapsed",
                    )
                    if checked:
                        new_selection.append((day, ts))

        st.markdown("<hr style='margin:8px 0;border-color:#f1f5f9;'>", unsafe_allow_html=True)

        col_btn, col_count = st.columns([2, 3])
        with col_btn:
            submitted = st.form_submit_button("Save Availability", type="primary", use_container_width=True)
        with col_count:
            st.markdown(
                f"<div style='padding:10px 0;color:#64748b;font-size:13px;'>"
                f"Saved: <b>{len(existing_avail)} slot(s)</b> &nbsp;·&nbsp; "
                f"Current selection: <b>{len(new_selection)}</b></div>",
                unsafe_allow_html=True,
            )

        if submitted:
            success = database.set_user_availability(user_id, new_selection)
            if success:
                # Bust matcher cache so new availability is reflected
                cache_key = f"matches_{user_id}"
                st.session_state.pop(cache_key, None)
                st.toast("Availability saved!", icon="📅")
                st.rerun()
            else:
                st.error("Could not save availability. Please try again.")

    # ── Peer overlap insight ──────────────────────────────────────────────────
    saved_avail = set(database.get_user_availability(user_id))
    if saved_avail:
        st.markdown("---")
        st.markdown("### Shared Availability with Top Matches")
        st.caption("Peers who share your free slots — great times to schedule sessions.")

        top_matches = MatcherService.get_top_matches(user_id)
        all_avail = database.get_all_availability()

        shown = 0
        for match in top_matches[:5]:
            mu = match['user']
            other_avail = set(all_avail.get(mu['id'], []))
            shared = saved_avail.intersection(other_avail)
            if shared:
                name = mu.get('name') or mu['username']
                shared_sorted = sorted(shared, key=lambda x: (DAYS.index(x[0]), TIMESLOTS.index(x[1])))
                shared_labels = [f"{d} {SLOT_ICONS[TIMESLOTS.index(s)]}" for d, s in shared_sorted]
                with st.container(border=True):
                    col1, col2 = st.columns([2, 3])
                    with col1:
                        st.markdown(
                            f"**{name}** &nbsp; "
                            f"<span style='color:#10b981;font-weight:700;'>{match['score']}%</span>",
                            unsafe_allow_html=True,
                        )
                        st.caption(mu.get('course') or "")
                    with col2:
                        pills = "".join(
                            f"<span class='tag-pill green' style='margin:2px;'>{lbl}</span>"
                            for lbl in shared_labels[:6]
                        )
                        if len(shared_labels) > 6:
                            pills += f"<span class='tag-pill'>+{len(shared_labels)-6} more</span>"
                        st.markdown(pills, unsafe_allow_html=True)
                shown += 1

        if shown == 0:
            st.info("None of your top matches have overlapping availability yet. "
                    "Ask them to update their schedule!")
