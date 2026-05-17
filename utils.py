"""Shared utility functions — single source of truth for helpers used across views."""

import streamlit as st
from datetime import date, timedelta
from config import DAYS, TIMESLOTS


# ── Avatar ────────────────────────────────────────────────────────────────────

def get_avatar_url(seed: str) -> str:
    return f"https://api.dicebear.com/7.x/adventurer/svg?seed={seed}&backgroundColor=b6e3f4,c0aede,d1d4f9"


# ── Priority helpers ──────────────────────────────────────────────────────────

def priority_color(priority: str) -> str:
    return {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}.get(priority, "#94a3b8")


def priority_icon(priority: str) -> str:
    return {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")


# ── Score display helpers ─────────────────────────────────────────────────────

def score_color(score: int) -> str:
    if score >= 70:
        return "#10b981"
    elif score >= 40:
        return "#f59e0b"
    else:
        return "#3b82f6"


def score_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Strong"
    elif score >= 40:
        return "Good"
    elif score >= 20:
        return "Moderate"
    else:
        return "Low"


# ── Profile completion ────────────────────────────────────────────────────────

def calculate_profile_completion(user: dict) -> int:
    """Returns a 0-100 profile completion score based on 11 profile fields."""
    checks = [
        bool(user.get('name')),
        bool(user.get('course')),
        bool(user.get('degree_level')),
        bool(user.get('university')),
        bool(user.get('campus')),
        bool(user.get('location_zone')),
        bool(user.get('subjects')),
        bool(user.get('goals')),
        bool(user.get('study_styles')),
        bool(user.get('study_environment')),
        bool(user.get('study_vibe')),
    ]
    return int(sum(checks) / len(checks) * 100)


# ── Match cache management ────────────────────────────────────────────────────

def invalidate_match_cache(user_id: int) -> None:
    """Bust the session-state match cache so the next render recomputes scores."""
    st.session_state.pop(f"matches_{user_id}", None)


# ── Calendar / ICS helpers ────────────────────────────────────────────────────

def _next_weekday(day_name: str) -> date:
    """Return the next calendar date for the given weekday name (never today)."""
    target = DAYS.index(day_name)
    today = date.today()
    days_ahead = (target - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + timedelta(days=days_ahead)


def _slot_hour(timeslot: str) -> int:
    """Map a TIMESLOTS string to a starting hour integer."""
    return {TIMESLOTS[0]: 9, TIMESLOTS[1]: 13, TIMESLOTS[2]: 18}.get(timeslot, 9)
