"""
auth/session.py — Login session management
==========================================
Thin wrapper around st.session_state for auth state.
All auth checks in app.py and pages go through these helpers
so the logic is in one place.

Session state keys used:
    user            dict  — {id, email, name, picture, role}
    oauth_token     dict  — raw OAuth token (not persisted to DB)
"""

from __future__ import annotations
import streamlit as st


# ── Setters ──────────────────────────────────────────────────────────────────

def login(user_record: dict):
    """Store a user record in session after successful OAuth."""
    st.session_state["user"] = user_record


def logout():
    """Clear all auth-related session state."""
    for key in ["user", "oauth_token", "session_token", "_cached_auth_url"]:
        st.session_state.pop(key, None)


def set_oauth_token(token: dict):
    st.session_state["oauth_token"] = token


def set_session_token(token: str):
    """Store the persistent (DB-backed) session token for this login."""
    st.session_state["session_token"] = token


def get_session_token() -> str | None:
    return st.session_state.get("session_token")


# ── Getters ──────────────────────────────────────────────────────────────────

def current_user() -> dict | None:
    """Return the logged-in user dict or None."""
    return st.session_state.get("user")


def is_logged_in() -> bool:
    return "user" in st.session_state and st.session_state["user"] is not None


def is_admin() -> bool:
    user = current_user()
    return user is not None and user.get("role") == "admin"


def get_oauth_token() -> dict | None:
    return st.session_state.get("oauth_token")


# ── Guards ────────────────────────────────────────────────────────────────────

def require_login():
    """
    Call at the top of any page that needs authentication.
    Stops rendering and shows a message if not logged in.
    """
    if not is_logged_in():
        st.warning("Please log in to access this page.")
        st.stop()


def require_admin():
    """
    Call at the top of any admin-only page.
    Stops rendering if user is not an admin.
    """
    require_login()
    if not is_admin():
        st.error("Access denied — admin only.")
        st.stop()
