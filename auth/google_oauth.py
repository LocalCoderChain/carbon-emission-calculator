"""
auth/google_oauth.py — Google OAuth 2.0 flow
=============================================
Handles the full Google SSO cycle:
  1. Build the authorization URL → redirect user to Google
  2. Exchange the returned code for tokens
  3. Fetch the user's profile (email, name, picture)

Dependencies:
    pip install requests-oauthlib
"""

from __future__ import annotations
import requests
from requests_oauthlib import OAuth2Session

# Google OAuth endpoints
_AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/auth"
_TOKEN_URL              = "https://oauth2.googleapis.com/token"
_USERINFO_URL           = "https://www.googleapis.com/oauth2/v3/userinfo"

_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def build_auth_url(client_id: str, redirect_uri: str) -> tuple[str, str]:
    """
    Build the Google authorization URL and return (auth_url, state).
    Store `state` in session to verify the callback.
    """
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=_SCOPES)
    auth_url, state = oauth.authorization_url(
        _AUTHORIZATION_BASE_URL,
        access_type="offline",
        prompt="select_account",   # always show account picker
    )
    return auth_url, state


def fetch_token(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    authorization_response: str,
    state: str,
) -> dict:
    """
    Exchange the authorization code for an access token.
    `authorization_response` is the full callback URL including the code.
    Returns the token dict.
    """
    import os
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"   # allow http in dev

    oauth = OAuth2Session(
        client_id,
        redirect_uri=redirect_uri,
        state=state,
        scope=_SCOPES,
    )
    token = oauth.fetch_token(
        _TOKEN_URL,
        authorization_response=authorization_response,
        client_secret=client_secret,
    )
    return token


def get_user_info(token: dict, client_id: str, redirect_uri: str) -> dict:
    """
    Use the access token to fetch the user's Google profile.
    Returns dict with keys: email, name, picture, sub (Google user ID)
    """
    import os
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    oauth = OAuth2Session(client_id, token=token)
    resp  = oauth.get(_USERINFO_URL)
    resp.raise_for_status()
    return resp.json()


_DEFAULT_LINK_CSS = (
    "display:inline-block;text-align:center;background:#00AEEF;color:#FFFFFF;"
    "padding:10px 24px;border-radius:4px;font-weight:600;text-decoration:none;"
    "font-family:Barlow,sans-serif;font-size:0.95rem;"
)


def get_or_create_auth_url(client_id: str, redirect_uri: str) -> str:
    """
    Return a cached (auth_url, state) pair for the current login attempt.

    A page can render the sign-in link in more than one spot in the same run
    (header + an inline "please sign in" prompt, for example). If each spot
    called build_auth_url() independently, each would mint its own random
    `state` and clobber the one saved in session — so whichever link the
    user actually clicks would no longer match what's stored, and Google's
    callback would fail with a state mismatch. Caching in session_state
    ensures every rendered link this login attempt shares the same URL/state.

    The state itself is persisted via OAuthStateManager (database-backed),
    not session_state — Google's redirect back to the app is a full page
    reload, which wipes session_state, so the CSRF check has to be able to
    survive that round trip independently of any particular browser session.

    The cached link is only reused while it's fresh. OAuthStateManager expires
    states after 10 minutes (see database/db.py), and this function is called
    on every script rerun (each widget interaction reruns the page), so a
    user who takes a while filling out the form before clicking "Sign in"
    would otherwise click a link whose state already expired server-side.
    Refreshing it here keeps the visible link's state valid.
    """
    import os
    import streamlit as st
    from datetime import datetime, timedelta
    from database.db import OAuthStateManager
    from config.settings import DB_CONFIG

    _REFRESH_AFTER_MINUTES = 8  # stay under OAuthStateManager's 10-minute TTL

    cached    = st.session_state.get("_cached_auth_url")
    cached_at = st.session_state.get("_cached_auth_url_at")
    if cached and cached_at and (datetime.now() - cached_at) < timedelta(minutes=_REFRESH_AFTER_MINUTES):
        return cached

    auth_url, oauth_state = build_auth_url(client_id, redirect_uri)
    db_path = os.path.abspath(DB_CONFIG.get("sqlite_path", "carbon_calculator.db"))
    OAuthStateManager(db_path).create(oauth_state)
    st.session_state["_cached_auth_url"] = auth_url
    st.session_state["_cached_auth_url_at"] = datetime.now()
    return auth_url


def render_signin_link(client_id: str, redirect_uri: str,
                        label: str = "Sign in with Google", css: str = _DEFAULT_LINK_CSS) -> None:
    """
    Render a Google sign-in link that navigates in the SAME tab (target="_self"),
    unlike st.link_button which always opens a new tab.
    """
    import streamlit as st

    auth_url = get_or_create_auth_url(client_id, redirect_uri)
    st.markdown(
        f'<a href="{auth_url}" target="_self" style="{css}">{label}</a>',
        unsafe_allow_html=True,
    )
