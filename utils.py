"""Shared utility functions."""


def get_avatar_url(seed: str) -> str:
    return f"https://api.dicebear.com/7.x/adventurer/svg?seed={seed}&backgroundColor=b6e3f4,c0aede,d1d4f9"


def priority_color(priority: str) -> str:
    return {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}.get(priority, "#94a3b8")


def priority_icon(priority: str) -> str:
    return {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(priority, "⚪")
