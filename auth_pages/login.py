"""
pages/login.py — Google SSO Login Page
=======================================
Handles the full OAuth dance:
  1. User clicks "Sign in with Google" → redirected to Google
  2. Google redirects back with ?code=... in the URL
  3. We exchange the code for a token, fetch profile, upsert user in DB
  4. Store user in session state → redirect to calculator

This page is rendered by app.py when the user is not logged in
and navigates to Login, OR when Google redirects back with a code.
"""

import os
import streamlit as st

from auth.google_oauth import fetch_token, get_user_info, render_signin_link
from auth import session
from database.db import UserManager, SessionManager, OAuthStateManager
from config.settings import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    ADMIN_EMAILS,
    DB_CONFIG,
)

import os
db_path = os.path.abspath(DB_CONFIG.get("sqlite_path", "carbon_calculator.db"))
um  = UserManager(db_path)
sm  = SessionManager(db_path)
osm = OAuthStateManager(db_path)


def render():
    """Main entry point — called from app.py."""

    st.markdown("""
    <style>
    .login-container {
        max-width: 420px;
        margin: 60px auto;
        background: #FFFFFF;
        border-radius: 12px;
        padding: 40px 36px;
        box-shadow: 0 4px 24px rgba(0,48,87,0.10);
        border-top: 4px solid #00AEEF;
        text-align: center;
    }
    .login-brand {
        font-family: 'Barlow Condensed', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: #003057;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }
    .login-sub {
        font-size: 0.78rem;
        color: #8DB0C8;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 28px;
    }
    .login-divider {
        border: none;
        border-top: 1px solid #DDE4EC;
        margin: 24px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Check if Google redirected back with a code ───────────────────────
    # Streamlit exposes URL query params via st.query_params
    params = st.query_params
    code  = params.get("code")
    state = params.get("state")

    if code and state:
        _handle_callback(code, state)
        return

    # ── Show login UI ─────────────────────────────────────────────────────
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("""
        <div class="login-container">
            <div class="login-brand">Atlas Copco</div>
            <div class="login-sub">Carbon Emission Calculator</div>
            <hr class="login-divider">
            <p style="font-size:0.9rem;color:#4A5F72;margin-bottom:24px;">
                Sign in with your Google account to access the calculator
                and save your calculations.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID == "your_client_id_here":
            st.error("Google OAuth is not configured. Add GOOGLE_CLIENT_ID to config/settings.py")
            return

        render_signin_link(
            GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI,
            label="Sign in with Google",
            css="display:block;width:100%;box-sizing:border-box;text-align:center;"
                "background:#00AEEF;color:#FFFFFF;padding:12px 28px;border-radius:4px;"
                "font-weight:600;text-decoration:none;font-family:Barlow,sans-serif;"
                "font-size:0.95rem;margin-top:8px;",
        )


def _handle_callback(code: str, returned_state: str):
    """Exchange code for token and log the user in."""
    if not osm.consume(returned_state):
        st.error("Login failed: state mismatch. Please try signing in again.")
        if st.button("Back to Login", key="back_login_state_mismatch"):
            st.session_state.pop("_cached_auth_url", None)
            st.query_params.clear()
            st.rerun()
        return

    # Build the full authorization_response URL
    # Streamlit doesn't expose the raw URL easily, so we reconstruct it
    base = GOOGLE_REDIRECT_URI.rstrip("/")
    authorization_response = (
        f"{base}/?code={code}&state={returned_state}"
    )

    with st.spinner("Signing you in…"):
        try:
            token = fetch_token(
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                redirect_uri=GOOGLE_REDIRECT_URI,
                authorization_response=authorization_response,
                state=returned_state,
            )
            session.set_oauth_token(token)

            user_info = get_user_info(token, GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI)
            email   = user_info.get("email", "")
            name    = user_info.get("name", email)
            picture = user_info.get("picture", "")

            # Upsert in DB and get back full record with role
            user_record = um.upsert_user(email, name, picture, ADMIN_EMAILS)
            session.login(user_record)

            # Create a persistent, DB-backed session so a page refresh (which
            # wipes st.session_state) can restore the login from the URL, and
            # so an admin can revoke this specific session later.
            session_token = sm.create_session(user_record["id"])
            session.set_session_token(session_token)

            # Clear the OAuth code from the URL, keep only the session token
            st.query_params.clear()
            st.query_params["session"] = session_token
            st.rerun()

        except Exception as e:
            st.error(f"Login failed: {e}")
            st.info("Please try again.")
            if st.button("Back to Login", key="back_login"):
                st.session_state.pop("_cached_auth_url", None)
                st.query_params.clear()
                st.rerun()
