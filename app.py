"""
app.py — Carbon Emission Calculator
Atlas Copco | Streamlit UI
v1.3 — Product templates, auto-distance, Google SSO, Admin panel
"""

import sys
import os

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import streamlit as st
import pandas as pd
from datetime import datetime

from auth import session as auth_session
from auth.google_oauth import render_signin_link
# Change these two lines at the top of app.py
from auth_pages import login as login_page
from auth_pages import admin as admin_page

from utils.formulas import (
    calculate_all,
    TRANSPORT_FACTORS,
    PLASTIC_EMISSION_FACTORS,
    EMISSION_FACTORS,
    BOX_CLEARANCE,
)
from utils.distance import get_distance
from database.db import DatabaseManager, ProductManager, UserManager, ConfigManager, SessionManager
from config.settings import (
    DB_CONFIG, APP_TITLE, APP_VERSION, BRAND,
    ORS_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI, ADMIN_EMAILS,
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Carbon Emission Calculator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700&family=Barlow+Condensed:wght@400;600;700&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], [data-testid="stToolbar"],
.main, .block-container {
    background-color: #F4F6F8 !important;
    color: #1A2B3C !important;
    font-family: 'Barlow', sans-serif !important;
}

input, textarea, select,
.stTextInput input, .stTextInput > div > div > input,
.stNumberInput input, .stNumberInput > div > div > input,
.stTextArea textarea, .stTextArea > div > div > textarea,
.stSelectbox > div > div > div, .stSelectbox select,
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea,
[data-baseweb="select"] div,
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background-color: #FFFFFF !important;
    color: #1A2B3C !important;
    border: 1.5px solid #C8D5E0 !important;
    border-radius: 4px !important;
    font-family: 'Barlow', sans-serif !important;
    font-size: 0.92rem !important;
    caret-color: #003057 !important;
    -webkit-text-fill-color: #1A2B3C !important;
}

[data-testid="stNumberInput"] > div,
[data-testid="stNumberInput"] > div > div,
.stNumberInput > div, .stNumberInput > div > div {
    background-color: #FFFFFF !important;
    border-radius: 4px !important;
}

[data-baseweb="select"] > div:first-child,
[data-baseweb="select"] [data-testid="stSelectbox"],
.stSelectbox > div > div {
    background-color: #FFFFFF !important;
    color: #1A2B3C !important;
    border: 1.5px solid #C8D5E0 !important;
    border-radius: 4px !important;
}

[data-baseweb="popover"] li, [data-baseweb="menu"] li,
[role="option"], [data-baseweb="select"] [role="option"] {
    background-color: #FFFFFF !important;
    color: #1A2B3C !important;
}
[data-baseweb="popover"] li:hover, [data-baseweb="menu"] li:hover,
[role="option"]:hover {
    background-color: #E8F6FD !important;
    color: #003057 !important;
}

[data-baseweb="select"] span,
[data-baseweb="select"] div[class*="ValueContainer"] span,
[data-baseweb="select"] div[class*="singleValue"] {
    color: #1A2B3C !important;
    -webkit-text-fill-color: #1A2B3C !important;
}

input:focus, textarea:focus,
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within {
    border-color: #00AEEF !important;
    box-shadow: 0 0 0 2px rgba(0,174,239,0.18) !important;
    outline: none !important;
}

.stNumberInput button, [data-testid="stNumberInput"] button {
    background-color: #F0F4F8 !important;
    color: #003057 !important;
    border: 1px solid #C8D5E0 !important;
}
.stNumberInput button:hover, [data-testid="stNumberInput"] button:hover {
    background-color: #00AEEF !important;
    color: #FFFFFF !important;
    border-color: #00AEEF !important;
}

label, .stTextInput label, .stNumberInput label, .stSelectbox label,
.stTextArea label, .stCheckbox label,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
p[data-testid="stWidgetLabel"] {
    color: #4A5F72 !important;
    font-size: 0.80rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
    font-family: 'Barlow', sans-serif !important;
    -webkit-text-fill-color: #4A5F72 !important;
}

.stCheckbox label, .stCheckbox [data-testid="stWidgetLabel"],
.stCheckbox [data-testid="stWidgetLabel"] p {
    text-transform: none !important;
    letter-spacing: 0 !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    color: #1A2B3C !important;
    -webkit-text-fill-color: #1A2B3C !important;
}

.stApp { background-color: #F4F6F8 !important; }
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
    background-color: #F4F6F8 !important;
}

section[data-testid="stSidebar"],
section[data-testid="stSidebar"] > div {
    background-color: #003057 !important;
    border-right: 3px solid #00AEEF;
}
section[data-testid="stSidebar"] * {
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stRadio [data-testid="stWidgetLabel"] p {
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    padding: 4px 0 !important;
    color: #CDDBE8 !important;
    -webkit-text-fill-color: #CDDBE8 !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
}
section[data-testid="stSidebar"] hr { border-color: rgba(0,174,239,0.3); }

.atlas-header {
    background: linear-gradient(135deg, #003057 0%, #005288 100%);
    padding: 20px 32px;
    border-radius: 8px;
    margin-bottom: 24px;
    border-left: 5px solid #00AEEF;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.atlas-header h1 {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 1.8rem;
    font-weight: 700;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    margin: 0;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.atlas-header .subtitle { color: #00AEEF; font-size: 0.85rem; font-weight: 400; margin-top: 4px; }
.atlas-header .logo-area { text-align: right; color: #8DB0C8; font-size: 0.75rem; font-weight: 500; letter-spacing: 1px; }

.section-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #003057;
    text-transform: uppercase;
    letter-spacing: 1px;
    border-bottom: 2px solid #00AEEF;
    padding-bottom: 8px;
    margin-bottom: 18px;
}
.sub-section-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: #00AEEF;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin: 14px 0 8px 0;
}

.metric-card {
    background: linear-gradient(135deg, #003057, #005288);
    border-radius: 8px;
    padding: 18px 20px;
    border-left: 4px solid #00AEEF;
    margin-bottom: 12px;
}
.metric-card .m-label { font-size: 0.75rem; color: #8DB0C8; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; }
.metric-card .m-value { font-family: 'Barlow Condensed', sans-serif; font-size: 2rem; color: #FFFFFF; font-weight: 700; line-height: 1.1; margin-top: 2px; }
.metric-card .m-unit  { font-size: 0.85rem; color: #00AEEF; font-weight: 500; }

.co2-card {
    background: linear-gradient(135deg, #003057, #00253F);
    border-radius: 10px;
    padding: 24px;
    border: 2px solid #00AEEF;
    text-align: center;
    margin: 16px 0;
}
.co2-card .co2-label { font-size: 0.78rem; color: #8DB0C8; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; }
.co2-card .co2-value { font-family: 'Barlow Condensed', sans-serif; font-size: 3.2rem; color: #00AEEF; font-weight: 700; line-height: 1; margin: 8px 0 4px; }
.co2-card .co2-unit  { font-size: 1rem; color: #FFFFFF; font-weight: 400; }

.stButton > button {
    background: #00AEEF !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    border: none !important;
    border-radius: 4px !important;
    font-family: 'Barlow', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    letter-spacing: 0.5px !important;
    padding: 10px 28px !important;
    transition: background 0.2s !important;
    text-transform: none !important;
    white-space: nowrap !important;
    overflow: visible !important;
    width: auto !important;
    min-width: fit-content !important;
}
.stButton > button:hover { background: #0097D1 !important; }

.stCheckbox > label > div[data-testid="stCheckbox"],
.stCheckbox span[data-testid="stCheckbox"] {
    background-color: #FFFFFF !important;
    border-color: #C8D5E0 !important;
}

hr { border-color: #DDE4EC; margin: 16px 0; }

.stDataFrame { border-radius: 8px; overflow: hidden; }
[data-testid="stDataFrameResizable"] { border: 1px solid #DDE4EC; border-radius: 8px; }

.info-box {
    background: #E8F6FD;
    border-left: 4px solid #00AEEF;
    padding: 12px 16px;
    border-radius: 4px;
    font-size: 0.84rem;
    color: #003057;
    margin: 10px 0;
}

.warn-box {
    background: #FFF8E1;
    border-left: 4px solid #F5A623;
    padding: 12px 16px;
    border-radius: 4px;
    font-size: 0.84rem;
    color: #7A5200;
    margin: 10px 0;
}

.compare-box {
    background: #003057;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    border: 1px solid #00AEEF;
}
.compare-box h3 {
    color: #00AEEF;
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.1rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
}
.compare-winner { font-family: 'Barlow Condensed', sans-serif; font-size: 1.5rem; font-weight: 700; color: #00A878; }

.sidebar-brand { padding: 8px 0 20px 0; text-align: center; }
.sidebar-brand .brand-name {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 1.6rem; font-weight: 700;
    color: #00AEEF !important; letter-spacing: 1px; display: block;
}
.sidebar-brand .brand-sub {
    font-size: 0.65rem; color: #8DB0C8 !important;
    letter-spacing: 2px; text-transform: uppercase; display: block; margin-top: 2px;
}
.sidebar-nav-label {
    font-size: 0.65rem; color: #8DB0C8 !important;
    text-transform: uppercase; letter-spacing: 2px;
    margin: 16px 0 6px 0; display: block; font-weight: 600;
}

.product-loaded-banner {
    background: linear-gradient(90deg, #003057, #005288);
    border: 1px solid #00AEEF;
    border-radius: 6px;
    padding: 10px 16px;
    font-size: 0.84rem;
    color: #FFFFFF;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE MANAGERS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    return DatabaseManager(DB_CONFIG)

@st.cache_resource
def get_pm():
    db_path = os.path.abspath(DB_CONFIG.get("sqlite_path", "carbon_calculator.db"))
    return ProductManager(db_path)

@st.cache_resource
def get_um():
    db_path = os.path.abspath(DB_CONFIG.get("sqlite_path", "carbon_calculator.db"))
    return UserManager(db_path)

@st.cache_resource
def get_cfg():
    db_path = os.path.abspath(DB_CONFIG.get("sqlite_path", "carbon_calculator.db"))
    return ConfigManager(db_path)

@st.cache_resource
def get_sm():
    db_path = os.path.abspath(DB_CONFIG.get("sqlite_path", "carbon_calculator.db"))
    return SessionManager(db_path)

db  = get_db()
pm  = get_pm()
um  = get_um()
cfg = get_cfg()
sm  = get_sm()


# ─────────────────────────────────────────────────────────────────────────────
# SESSION RESTORE / VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
# A browser refresh wipes st.session_state, which would normally sign the
# user out. To survive that, the session token lives in the URL query string
# too, and gets validated against the DB on every run — this also lets an
# admin revoke a specific session and have it take effect immediately.
def _sync_session():
    token = auth_session.get_session_token()

    if not token:
        token = st.query_params.get("session")
        if not token:
            return
        record = sm.get_session(token)
        if record and not record["revoked"]:
            user = um.get_user_by_id(record["user_id"])
            if user:
                auth_session.login(user)
                auth_session.set_session_token(token)
                sm.touch(token)
                return
        st.query_params.pop("session", None)
        return

    record = sm.get_session(token)
    if not record or record["revoked"]:
        auth_session.logout()
        st.query_params.pop("session", None)
        st.warning("Your session was ended by an administrator. Please sign in again.")
    else:
        sm.touch(token)

_sync_session()


def _sign_out(token: str | None):
    if token:
        sm.delete_session(token)
    auth_session.logout()
    st.query_params.pop("session", None)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _pf(key: str, fallback=None):
    return st.session_state.get(f"pf_{key}", fallback)

def _load_product_into_state(fields: dict):
    for k, v in fields.items():
        if v is not None:
            st.session_state[f"pf_{k}"] = v
    st.session_state["product_loaded_name"] = fields.get("product_name", "")

def render_auth_header():
    user = auth_session.current_user()
    header_cols = st.columns([6, 1])
    with header_cols[1]:
        if user:
            role_badge = "🛡 Admin" if user.get("role") == "admin" else "👤"
            with st.popover(f"{role_badge} {user.get('name', 'User').split()[0]}"):
                st.markdown(f"**{user.get('name')}**")
                st.markdown(f"*{user.get('email')}*")
                st.markdown(f"Role: `{user.get('role')}`")
                st.markdown("---")
                if st.button("Sign Out", key="signout_btn"):
                    _sign_out(auth_session.get_session_token())
                    st.rerun()
        else:
            if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_ID != "your_client_id_here":
                render_signin_link(
                    GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI,
                    label="Sign In",
                    css="display:block;width:100%;box-sizing:border-box;text-align:center;"
                        "background:#00AEEF;color:#FFFFFF;padding:10px 0;border-radius:4px;"
                        "font-weight:600;text-decoration:none;font-family:Barlow,sans-serif;"
                        "font-size:0.95rem;",
                )
            elif st.button("Sign In", key="signin_header_btn", use_container_width=True):
                st.session_state["show_login_page"] = True
                st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <span class="brand-name">Atlas Copco</span>
        <span class="brand-sub">Carbon Emission Calculator</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<span class="sidebar-nav-label">Navigation</span>', unsafe_allow_html=True)

    _user = auth_session.current_user()
    nav_options = ["Calculate Carbon Emissions", "My Calculations", "Product Catalog", "Settings"]
    if _user and _user.get("role") == "admin":
        nav_options.append("Admin")

    page = st.radio("", nav_options, key="nav_page", label_visibility="collapsed")

    st.markdown("---")
    ok, msg = db.test_connection()
    if ok:
        st.markdown('<div style="font-size:0.72rem;color:#00A878;">◆ &nbsp;Database Connected</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:0.72rem;color:#F5A623;">◆ &nbsp;SQLite (local)</div>',
                    unsafe_allow_html=True)

    if ORS_API_KEY:
        st.markdown('<div style="font-size:0.72rem;color:#00A878;margin-top:4px;">◆ &nbsp;Auto-Distance Active</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:0.72rem;color:#8DB0C8;margin-top:4px;">◆ &nbsp;Auto-Distance Off</div>',
                    unsafe_allow_html=True)

    if _user:
        st.markdown(
            f'<div style="font-size:0.72rem;color:#00A878;margin-top:4px;">◆ &nbsp;'
            f'Signed in as {_user.get("name","").split()[0]}</div>',
            unsafe_allow_html=True
        )
        if st.button("Sign Out", key="signout_sidebar_btn", use_container_width=True):
            _sign_out(auth_session.get_session_token())
            st.rerun()

    st.markdown(f"""
    <div style="margin-top:32px;font-size:0.68rem;color:#4A6277;text-align:center;
                border-top:1px solid rgba(0,174,239,0.2);padding-top:12px;">
        v{APP_VERSION} &nbsp;·&nbsp; Atlas Copco Confidential
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# AUTH HEADER + MAIN HEADER
# ─────────────────────────────────────────────────────────────────────────────
render_auth_header()

st.markdown("""
<div class="atlas-header">
    <div>
        <h1>Calculate Carbon Emissions</h1>
        <div class="subtitle">Packaging &amp; Transport &nbsp;·&nbsp; Sustainability Intelligence Platform</div>
    </div>
    <div class="logo-area">
        ATLAS COPCO
        <div style="color:#00AEEF;font-size:2rem;font-weight:700;
                    font-family:'Barlow Condensed',sans-serif;line-height:1;margin-top:4px;">
            CO&#8322;
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DISTANCE WIDGET HELPER
# ─────────────────────────────────────────────────────────────────────────────
def distance_widget(section_key: str, transport_type: str, default_distance: float = 1000.0) -> float:
    st.markdown('<div class="sub-section-title">Route</div>', unsafe_allow_html=True)

    default_origin = _pf(f"{section_key}_origin", "")
    default_dest   = _pf(f"{section_key}_destination", "")

    if ORS_API_KEY:
        r1, r2 = st.columns(2)
        with r1:
            origin = st.text_input(
                "Origin (city / address)",
                value=default_origin,
                placeholder="e.g. Pune, India",
                key=f"origin_{section_key}",
            )
        with r2:
            destination = st.text_input(
                "Destination (city / address)",
                value=default_dest,
                placeholder="e.g. Frankfurt, Germany",
                key=f"dest_{section_key}",
            )

        auto_calc = st.button("Calculate Distance", key=f"calc_dist_{section_key}")

        if auto_calc and origin and destination:
            with st.spinner("Calculating route…"):
                km, msg = get_distance(origin, destination, transport_type, ORS_API_KEY)
            if km is not None:
                st.session_state[f"auto_km_{section_key}"] = km
                st.markdown(f'<div class="info-box">{msg}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="warn-box">{msg}</div>', unsafe_allow_html=True)
        elif auto_calc:
            st.markdown('<div class="warn-box">Please enter both origin and destination.</div>',
                        unsafe_allow_html=True)

        auto_km = st.session_state.get(f"auto_km_{section_key}", None)
        if auto_km is None:
            st.markdown(
                '<div class="info-box">Enter origin and destination above, '
                'then click <b>Calculate Distance</b> to auto-fill.</div>',
                unsafe_allow_html=True
            )
            distance_km = 0.0
        else:
            distance_km = st.number_input(
                "Distance (km) — edit to override",
                min_value=0.0,
                value=float(auto_km),
                step=10.0,
                format="%.0f",
                key=f"dist_km_{section_key}",
            )
    else:
        st.markdown(
            '<div class="info-box">Automatic distance is off. '
            'Add your free OpenRouteService API key in <code>config/settings.py</code>.</div>',
            unsafe_allow_html=True
        )
        distance_km = st.number_input(
            "Distance (km)",
            min_value=0.0,
            value=default_distance,
            step=50.0,
            format="%.0f",
            key=f"dist_km_{section_key}",
        )

    return float(distance_km)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE ROUTING
# ═════════════════════════════════════════════════════════════════════════════

_oauth_callback_pending = bool(st.query_params.get("code")) and bool(st.query_params.get("state"))

if _oauth_callback_pending or st.session_state.get("show_login_page"):
    st.session_state["show_login_page"] = False
    login_page.render()

elif page == "Admin":
    admin_page.render()

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 1 — CALCULATOR
# ═════════════════════════════════════════════════════════════════════════════
elif page == "Calculate Carbon Emissions":

    if not auth_session.current_user() and not st.session_state.get("dismiss_signin_banner"):
        banner_col, dismiss_col = st.columns([20, 1])
        with banner_col:
            st.markdown(
                '<div class="info-box">You can explore the calculator without signing in, '
                'but you\'ll need to <b>Sign In</b> (top right) to run a calculation and save results.</div>',
                unsafe_allow_html=True,
            )
        with dismiss_col:
            if st.button("✕", key="dismiss_signin_banner_btn", help="Dismiss"):
                st.session_state["dismiss_signin_banner"] = True
                st.rerun()

    # Product Template Loader
    products = pm.list_products()
    with st.expander(
        f"Load a saved product template ({len(products)} saved)" if products
        else "Load a saved product template — none saved yet",
        expanded=False,
    ):
        if products:
            product_names = [p["name"] for p in products]
            chosen = st.selectbox(
                "Select product",
                ["— select —"] + product_names,
                key="product_chooser",
            )
            load_col, clear_col = st.columns([1, 1])
            with load_col:
                if st.button("Load Selected Product", key="load_product_btn"):
                    if chosen != "— select —":
                        data = pm.load_product(chosen)
                        if data:
                            _load_product_into_state(data)
                            st.success(f"Loaded '{chosen}' — fields pre-filled below.")
                            st.rerun()
                        else:
                            st.error("Product not found.")
            with clear_col:
                if st.button("Clear Pre-fill", key="clear_prefill_btn"):
                    for k in list(st.session_state.keys()):
                        if k.startswith("pf_") or k == "product_loaded_name":
                            del st.session_state[k]
                    st.rerun()
        else:
            st.markdown(
                '<div class="info-box">No products saved yet. '
                'After calculating, use the <b>Save as Product Template</b> '
                'option that appears below the results.</div>',
                unsafe_allow_html=True,
            )

    if st.session_state.get("product_loaded_name"):
        st.markdown(
            f'<div class="product-loaded-banner">'
            f'<span style="color:#00AEEF;font-size:1.1rem">◈</span>'
            f'&nbsp; Product template loaded: '
            f'<b>{st.session_state["product_loaded_name"]}</b>'
            f'&nbsp;— modify any field and recalculate.</div>',
            unsafe_allow_html=True,
        )

    # Project Identity
    with st.container(border=True):
        st.markdown('<div class="section-title">Project Identity</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            pc_name = st.text_input(
                "PC / Project Code",
                value=_pf("pc_name", ""),
                placeholder="e.g. ABC-2024",
            )
        with c2:
            product_name = st.text_input(
                "Product Name",
                value=_pf("product_name", ""),
                placeholder="e.g. Compressor GA45",
            )
            if product_name.strip():
                existing = [p["name"] for p in pm.list_products()]
                matches  = [p for p in existing if product_name.strip().lower() in p.lower()]
                if matches:
                    st.markdown(
                        f'<div class="warn-box">⚠ Template exists: <b>{matches[0]}</b>. '
                        f'Use <b>Load Product</b> above to pre-fill all fields.</div>',
                        unsafe_allow_html=True
                    )

    left_col, right_col = st.columns([1, 1], gap="large")

    # ── LEFT — DESIGN CALCULATION ──
    with left_col:
        with st.container(border=True):
            st.markdown(
                '<div class="section-title">Design Calculation'
                '<span style="font-size:0.7rem;font-weight:400;color:#8D9BAD;'
                'margin-left:10px;text-transform:none;letter-spacing:0">'
                "If you don't know the weight of your packaging material</span></div>",
                unsafe_allow_html=True
            )

            st.markdown('<div class="sub-section-title">Product Size (mm)</div>', unsafe_allow_html=True)
            d1, d2, d3 = st.columns(3)
            with d1:
                length_mm = st.number_input("Length", min_value=0.0,
                    value=_pf("length_mm", 600.0), step=10.0, format="%.1f")
            with d2:
                width_mm = st.number_input("Width", min_value=0.0,
                    value=_pf("width_mm", 400.0), step=10.0, format="%.1f")
            with d3:
                height_mm = st.number_input("Height", min_value=0.0,
                    value=_pf("height_mm", 300.0), step=10.0, format="%.1f")

            st.markdown(
                f'<div class="info-box">+{BOX_CLEARANCE} mm clearance added automatically '
                f'to each dimension so the box fits safely around the product.</div>',
                unsafe_allow_html=True
            )

            st.markdown("---")

            st.markdown('<div class="sub-section-title">Box Type</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="info-box">Select ONE box type — corrugated and wooden box '
                'are alternatives. The chosen box sits on top of the pallet.</div>',
                unsafe_allow_html=True
            )
            _box_default = _pf("box_choice", "Corrugated Box")
            _box_idx     = 0 if _box_default == "Corrugated Box" else 1
            box_choice = st.radio(
                "Box Type",
                ["Corrugated Box", "Wooden Box"],
                index=_box_idx,
                horizontal=True,
                label_visibility="collapsed",
                key="box_choice",
            )
            use_corrugated = (box_choice == "Corrugated Box")
            use_wooden     = (box_choice == "Wooden Box")

            _ply_default   = _pf("ply", 5)
            _fefco_opts    = ["FEFCO 201", "FEFCO 200", "FEFCO 310"]
            _fefco_default = _pf("fefco_type", _fefco_opts[0])
            if use_corrugated:
                st.markdown('<div class="sub-section-title">Corrugated Box Properties</div>',
                            unsafe_allow_html=True)
                fefco_type = st.selectbox(
                    "Box Type", _fefco_opts,
                    index=_fefco_opts.index(_fefco_default) if _fefco_default in _fefco_opts else 0,
                    key="fefco_type",
                )
                ply = st.selectbox(
                    "Box Ply", [3, 5, 7],
                    index=[3, 5, 7].index(_ply_default) if _ply_default in [3, 5, 7] else 1
                )
            else:
                fefco_type = _fefco_default
                ply = 5

            if use_wooden:
                st.markdown('<div class="sub-section-title">Wooden Box Properties</div>',
                            unsafe_allow_html=True)
                bw1, bw2 = st.columns(2)
                with bw1:
                    thickness_mm = st.number_input(
                        "Box Thickness (mm)",
                        min_value=1.0, value=_pf("thickness_mm", 20.0), step=1.0, format="%.0f"
                    )
                with bw2:
                    _wt_opts    = ["Solidwood", "Plywood"]
                    _wt_default = _pf("wood_type_box", "Solidwood")
                    wood_type_box = st.selectbox(
                        "Wood Type (Box)", _wt_opts,
                        index=_wt_opts.index(_wt_default) if _wt_default in _wt_opts else 0,
                        key="wt_box",
                    )
            else:
                thickness_mm  = _pf("thickness_mm", 20.0)
                wood_type_box = _pf("wood_type_box", "Solidwood")

            st.markdown("---")

            st.markdown('<div class="sub-section-title">Wooden Pallet</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="info-box">Pallet dimensions auto-calculated from product size. '
                'Fixed: Deck H=36mm · Runner 125×110×90mm (×9) · Planks W×90×20mm (×3)</div>',
                unsafe_allow_html=True
            )
            _wtp_opts    = ["Plywood", "Solidwood"]
            _wtp_default = _pf("wood_type_pallet", "Plywood")
            wood_type_pallet = st.selectbox(
                "Wood Type (Pallet)", _wtp_opts,
                index=_wtp_opts.index(_wtp_default) if _wtp_default in _wtp_opts else 0,
                key="wt_pallet",
            )

            st.markdown("---")

            st.markdown('<div class="sub-section-title">Transportation</div>', unsafe_allow_html=True)
            _td_opts    = list(TRANSPORT_FACTORS.keys())
            _td_default = _pf("transport_design", _td_opts[0])
            transport_design = st.selectbox(
                "Transport Type", _td_opts,
                index=_td_opts.index(_td_default) if _td_default in _td_opts else 0,
                key="trans_design",
            )
            product_weight_kg = st.number_input(
                "Product Weight (kg)", min_value=0.0,
                value=_pf("product_weight_kg", 10.0), step=0.5, format="%.1f"
            )
            distance_design_km = distance_widget(
                section_key="design",
                transport_type=transport_design,
                default_distance=_pf("distance_design_km", 1000.0),
            )

    # ── RIGHT — PHYSICAL INPUT ──
    with right_col:
        with st.container(border=True):
            st.markdown(
                '<div class="section-title">Physical Input'
                '<span style="font-size:0.7rem;font-weight:400;color:#8D9BAD;'
                'margin-left:10px;text-transform:none;letter-spacing:0">'
                "If you know the weight of your packaging material</span></div>",
                unsafe_allow_html=True
            )

            st.markdown('<div class="sub-section-title">Material Weights (kg)</div>', unsafe_allow_html=True)
            p1, p2 = st.columns(2)
            with p1:
                phys_corrugated_kg = st.number_input(
                    "Corrugated Box (kg)", min_value=0.0,
                    value=_pf("phys_corrugated_kg", 0.0),
                    step=0.1, key="phys_corr", format="%.3f"
                )
                phys_wooden_kg = st.number_input(
                    "Wooden Box (kg)", min_value=0.0,
                    value=_pf("phys_wooden_kg", 0.0),
                    step=0.1, key="phys_wood", format="%.3f"
                )
            with p2:
                phys_pallet_kg = st.number_input(
                    "Wooden Pallet (kg)", min_value=0.0,
                    value=_pf("phys_pallet_kg", 0.0),
                    step=0.1, key="phys_pallet", format="%.3f"
                )
                phys_plastic_kg = st.number_input(
                    "Plastic Material (kg)", min_value=0.0,
                    value=_pf("phys_plastic_kg", 0.0),
                    step=0.1, key="phys_plastic", format="%.3f"
                )

            st.markdown('<div class="sub-section-title">Plastic Type</div>', unsafe_allow_html=True)
            _pt_opts    = list(PLASTIC_EMISSION_FACTORS.keys())
            _pt_default = _pf("phys_plastic_type", "LDPE")
            phys_plastic_type = st.selectbox(
                "Plastic Type", _pt_opts,
                index=_pt_opts.index(_pt_default) if _pt_default in _pt_opts else 0,
                key="phys_ptype",
            )
            plastic_info = {
                "LDPE":  "Low Density Polyethylene — shrink wrap, bags · 2.792 kgCO₂/kg",
                "HDPE":  "High Density Polyethylene — rigid containers · 2.506 kgCO₂/kg (lowest CO₂)",
                "PP":    "Polypropylene — strapping, rigid boxes · 3.576 kgCO₂/kg (highest CO₂)",
                "LLDPE": "Linear Low Density Polyethylene — pallet wrap · 2.587 kgCO₂/kg",
                "PS":    "Polystyrene — foam inserts, EPS packaging · 2.982 kgCO₂/kg",
            }
            st.markdown(
                f'<div class="info-box">{plastic_info.get(phys_plastic_type, "")}</div>',
                unsafe_allow_html=True
            )

            st.markdown('<div class="sub-section-title">Wood Type (Physical)</div>',
                        unsafe_allow_html=True)
            _pwt_opts    = ["Solidwood", "Plywood"]
            _pwt_default = _pf("phys_wood_type", "Solidwood")
            phys_wood_type = st.selectbox(
                "Wood Type (Physical)", _pwt_opts,
                index=_pwt_opts.index(_pwt_default) if _pwt_default in _pwt_opts else 0,
                key="phys_wt",
            )
            st.markdown(
                '<div class="info-box">Wood type for your physical wooden box and pallet. '
                'Solidwood = 0.31 kgCO₂/kg · Plywood = 0.68 kgCO₂/kg</div>',
                unsafe_allow_html=True,
            )

            st.markdown("---")

            st.markdown('<div class="sub-section-title">Packaging Combination (for Transport)</div>',
                        unsafe_allow_html=True)
            st.markdown(
                '<div class="info-box">Which box type is being shipped on the pallet? '
                'Sets the combined weight for transport CO₂. (Excel S18/S19)</div>',
                unsafe_allow_html=True
            )
            _combo_default = _pf("phys_pkg_combo", "corrugated+pallet")
            _combo_idx     = 0 if _combo_default == "corrugated+pallet" else 1
            phys_pkg_combo = st.radio(
                "Packaging combination",
                ["corrugated+pallet", "wooden+pallet"],
                index=_combo_idx,
                format_func=lambda x: "Corrugated Box + Pallet" if x == "corrugated+pallet"
                                      else "Wooden Box + Pallet",
                key="phys_combo",
                label_visibility="collapsed"
            )

            st.markdown("---")

            st.markdown('<div class="sub-section-title">Transportation</div>', unsafe_allow_html=True)
            _tp_opts    = list(TRANSPORT_FACTORS.keys())
            _tp_default = _pf("transport_physical", _tp_opts[0])
            transport_physical = st.selectbox(
                "Transport Type", _tp_opts,
                index=_tp_opts.index(_tp_default) if _tp_default in _tp_opts else 0,
                key="trans_phys",
            )
            phys_product_weight_kg = st.number_input(
                "Product Weight (kg)", min_value=0.0,
                value=_pf("phys_product_weight_kg", 0.0),
                step=0.5, key="phys_prod_wt", format="%.1f"
            )
            distance_physical_km = distance_widget(
                section_key="physical",
                transport_type=transport_physical,
                default_distance=_pf("distance_physical_km", 1000.0),
            )

    # Pre-calculate for auto note
    results = calculate_all(
        length_mm=length_mm, width_mm=width_mm, height_mm=height_mm,
        ply=ply, box_thickness_mm=thickness_mm,
        wood_type_box=wood_type_box, wood_type_pallet=wood_type_pallet,
        use_corrugated=use_corrugated, use_wooden=use_wooden,
        transport_type_design=transport_design,
        product_weight_kg=product_weight_kg,
        distance_design_km=distance_design_km,
        phys_corrugated_kg=phys_corrugated_kg,
        phys_wooden_kg=phys_wooden_kg,
        phys_pallet_kg=phys_pallet_kg,
        phys_plastic_kg=phys_plastic_kg,
        phys_plastic_type=phys_plastic_type,
        phys_wood_type_box=phys_wood_type,
        phys_packaging_combo=phys_pkg_combo,
        transport_type_physical=transport_physical,
        phys_product_weight_kg=phys_product_weight_kg,
        distance_physical_km=distance_physical_km,
    )

    auto_note = (
        f"Shipment of {product_name or 'product'} ({pc_name or 'N/A'}) "
        f"from {st.session_state.get('origin_design', '—')} "
        f"to {st.session_state.get('dest_design', '—')}. "
        f"Packaging: {box_choice}, {transport_design} transport over "
        f"{distance_design_km:.0f} km. "
        f"Total CO₂: {results['co2_total_design']:.4f} kg (Design), "
        f"{results['co2_total_phys']:.4f} kg (Physical)."
    )

    with st.container(border=True):
        st.markdown('<div class="section-title">Notes / Description</div>', unsafe_allow_html=True)
        note = st.text_area(
            "Add a note for this calculation",
            value=auto_note,
            height=80,
            label_visibility="collapsed"
        )

    _, btn_col, _ = st.columns([2, 1, 2])
    with btn_col:
        calc_clicked = st.button("CALCULATE", use_container_width=True)

    if calc_clicked and not auth_session.current_user():
        st.error("Please sign in with Google to run and save a calculation.")
        if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_ID != "your_client_id_here":
            _, gate_col, _ = st.columns([2, 1, 2])
            with gate_col:
                render_signin_link(GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI, label="Sign in with Google")
        calc_clicked = False

    if calc_clicked:
        results = calculate_all(
            length_mm=length_mm, width_mm=width_mm, height_mm=height_mm,
            ply=ply, box_thickness_mm=thickness_mm,
            wood_type_box=wood_type_box, wood_type_pallet=wood_type_pallet,
            use_corrugated=use_corrugated, use_wooden=use_wooden,
            transport_type_design=transport_design,
            product_weight_kg=product_weight_kg,
            distance_design_km=distance_design_km,
            phys_corrugated_kg=phys_corrugated_kg,
            phys_wooden_kg=phys_wooden_kg,
            phys_pallet_kg=phys_pallet_kg,
            phys_plastic_kg=phys_plastic_kg,
            phys_plastic_type=phys_plastic_type,
            phys_wood_type_box=phys_wood_type,
            phys_packaging_combo=phys_pkg_combo,
            transport_type_physical=transport_physical,
            phys_product_weight_kg=phys_product_weight_kg,
            distance_physical_km=distance_physical_km,
        )

        st.session_state["last_inputs"] = {
            "pc_name": pc_name, "product_name": product_name,
            "length_mm": length_mm, "width_mm": width_mm, "height_mm": height_mm,
            "box_choice": box_choice, "fefco_type": fefco_type, "ply": ply, "thickness_mm": thickness_mm,
            "wood_type_box": wood_type_box, "wood_type_pallet": wood_type_pallet,
            "transport_design": transport_design,
            "product_weight_kg": product_weight_kg,
            "distance_design_km": distance_design_km,
            "phys_corrugated_kg": phys_corrugated_kg,
            "phys_wooden_kg": phys_wooden_kg,
            "phys_pallet_kg": phys_pallet_kg,
            "phys_plastic_kg": phys_plastic_kg,
            "phys_plastic_type": phys_plastic_type,
            "phys_wood_type": phys_wood_type,
            "phys_pkg_combo": phys_pkg_combo,
            "transport_physical": transport_physical,
            "phys_product_weight_kg": phys_product_weight_kg,
            "distance_physical_km": distance_physical_km,
            "design_origin":        st.session_state.get("origin_design", ""),
            "design_destination":   st.session_state.get("dest_design", ""),
            "physical_origin":      st.session_state.get("origin_physical", ""),
            "physical_destination": st.session_state.get("dest_physical", ""),
        }

        st.markdown("---")
        st.markdown(
            '<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.2rem;'
            'font-weight:700;color:#003057;text-transform:uppercase;letter-spacing:1.5px;'
            'margin-bottom:14px;">Calculation Results</div>',
            unsafe_allow_html=True
        )

        res_left, res_right = st.columns(2, gap="large")

        with res_left:
            st.markdown('<div class="section-title">Design Calculation — Outputs</div>',
                        unsafe_allow_html=True)
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f"""<div class="metric-card">
                    <div class="m-label">Corr. Box Area</div>
                    <div class="m-value">{results['corr_area_m2']:.4f}</div>
                    <div class="m-unit">m²</div></div>""", unsafe_allow_html=True)
            with m2:
                st.markdown(f"""<div class="metric-card">
                    <div class="m-label">Corr. Box Weight</div>
                    <div class="m-value">{results['corr_weight_kg']:.3f}</div>
                    <div class="m-unit">kg</div></div>""", unsafe_allow_html=True)
            with m3:
                st.markdown(f"""<div class="metric-card">
                    <div class="m-label">Wooden Box Weight</div>
                    <div class="m-value">{results['wood_weight_kg']:.3f}</div>
                    <div class="m-unit">kg</div></div>""", unsafe_allow_html=True)
            m4, m5, m6 = st.columns(3)
            with m4:
                st.markdown(f"""<div class="metric-card">
                    <div class="m-label">Pallet Volume</div>
                    <div class="m-value">{results['pallet_vol_m3']:.6f}</div>
                    <div class="m-unit">m³</div></div>""", unsafe_allow_html=True)
            with m5:
                st.markdown(f"""<div class="metric-card">
                    <div class="m-label">Pallet Weight</div>
                    <div class="m-value">{results['pallet_wt_kg']:.3f}</div>
                    <div class="m-unit">kg</div></div>""", unsafe_allow_html=True)
            with m6:
                st.markdown(f"""<div class="metric-card">
                    <div class="m-label">Total Ship. Wt</div>
                    <div class="m-value">{results['design_total_weight_kg']:.2f}</div>
                    <div class="m-unit">kg</div></div>""", unsafe_allow_html=True)

            st.markdown('<div class="sub-section-title" style="margin-top:16px">CO₂ Breakdown</div>',
                        unsafe_allow_html=True)
            active_box = "Corrugated Box" if use_corrugated else "Wooden Box"
            df_design = pd.DataFrame({
                "Source": [active_box, "Wooden Pallet", f"Transport — {transport_design}"],
                "CO₂ (kg)": [
                    round(results["co2_corr_design"] + results["co2_wood_design"], 4),
                    round(results["co2_pallet_design"], 4),
                    round(results["co2_transport_design"], 4),
                ]
            })
            st.dataframe(df_design, use_container_width=True, hide_index=True)
            st.markdown(f"""<div class="co2-card">
                <div class="co2-label">Total CO₂ — Design Calculation</div>
                <div class="co2-value">{results['co2_total_design']:.4f}</div>
                <div class="co2-unit">kg CO₂ equivalent</div>
            </div>""", unsafe_allow_html=True)

        with res_right:
            st.markdown('<div class="section-title">Physical Input — Outputs</div>',
                        unsafe_allow_html=True)
            pm1, pm2, pm3 = st.columns(3)
            with pm1:
                st.markdown(f"""<div class="metric-card">
                    <div class="m-label">Packaging Weight</div>
                    <div class="m-value">{results['phys_pkg_wt']:.3f}</div>
                    <div class="m-unit">kg</div></div>""", unsafe_allow_html=True)
            with pm2:
                st.markdown(f"""<div class="metric-card">
                    <div class="m-label">Total Shipment</div>
                    <div class="m-value">{results['phys_total_weight_kg']:.3f}</div>
                    <div class="m-unit">kg</div></div>""", unsafe_allow_html=True)
            with pm3:
                st.markdown(f"""<div class="metric-card">
                    <div class="m-label">Transport CO₂</div>
                    <div class="m-value">{results['co2_transport_phys']:.4f}</div>
                    <div class="m-unit">kg</div></div>""", unsafe_allow_html=True)

            st.markdown('<div class="sub-section-title" style="margin-top:16px">CO₂ Breakdown</div>',
                        unsafe_allow_html=True)
            df_phys = pd.DataFrame({
                "Source": [
                    "Corrugated Box", "Wood (Box + Pallet)",
                    f"Plastic — {phys_plastic_type}", f"Transport — {transport_physical}",
                ],
                "CO₂ (kg)": [
                    round(results["co2_corr_phys"], 4),
                    round(results["co2_wood_phys"], 4),
                    round(results["co2_plastic_phys"], 4),
                    round(results["co2_transport_phys"], 4),
                ]
            })
            st.dataframe(df_phys, use_container_width=True, hide_index=True)
            st.markdown(f"""<div class="co2-card">
                <div class="co2-label">Total CO₂ — Physical Input</div>
                <div class="co2-value">{results['co2_total_phys']:.4f}</div>
                <div class="co2-unit">kg CO₂ equivalent</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("---")
        d_total = results["co2_total_design"]
        p_total = results["co2_total_phys"]
        winner  = "Design Calculation" if d_total <= p_total else "Physical Input"
        saving  = abs(d_total - p_total)
        _, cmp_col, _ = st.columns([1, 2, 1])
        with cmp_col:
            st.markdown(f"""<div class="compare-box">
                <h3>Sustainability Comparison</h3>
                <div class="compare-winner">{winner}</div>
                <div style="color:#8DB0C8;font-size:0.85rem;margin-top:8px;">
                    Lower by <b style="color:#00AEEF">{saving:.4f} kg CO₂</b>
                </div>
                <div style="margin-top:14px;display:flex;justify-content:center;gap:24px">
                    <div style="text-align:center">
                        <div style="font-size:0.72rem;color:#8DB0C8;text-transform:uppercase">Design</div>
                        <div style="font-size:1.4rem;font-weight:700;color:#FFFFFF;
                                    font-family:'Barlow Condensed',sans-serif">{d_total:.4f}</div>
                        <div style="font-size:0.72rem;color:#8DB0C8">kg CO₂</div>
                    </div>
                    <div style="color:#00AEEF;font-size:1.5rem;align-self:center">vs</div>
                    <div style="text-align:center">
                        <div style="font-size:0.72rem;color:#8DB0C8;text-transform:uppercase">Physical</div>
                        <div style="font-size:1.4rem;font-weight:700;color:#FFFFFF;
                                    font-family:'Barlow Condensed',sans-serif">{p_total:.4f}</div>
                        <div style="font-size:0.72rem;color:#8DB0C8">kg CO₂</div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        # Save calculation to DB
        inputs_to_save = {
            "pc_name": pc_name, "product_name": product_name,
            "length_mm": length_mm, "width_mm": width_mm, "height_mm": height_mm,
            "box_choice": box_choice, "fefco_type": fefco_type, "ply": ply, "thickness_mm": thickness_mm,
            "wood_type_box": wood_type_box, "wood_type_pallet": wood_type_pallet,
            "transport_design": transport_design,
            "product_weight_kg": product_weight_kg,
            "distance_design_km": distance_design_km,
            "phys_corrugated_kg": phys_corrugated_kg,
            "phys_wooden_kg": phys_wooden_kg,
            "phys_pallet_kg": phys_pallet_kg,
            "phys_plastic_kg": phys_plastic_kg,
            "phys_plastic_type": phys_plastic_type,
            "phys_wood_type": phys_wood_type,
            "phys_pkg_combo": phys_pkg_combo,
            "transport_physical": transport_physical,
            "phys_product_weight_kg": phys_product_weight_kg,
            "distance_physical_km": distance_physical_km,
        }
        outputs_to_save = {k: round(v, 6) if isinstance(v, float) else v
                           for k, v in results.items()}
        try:
            current_user = auth_session.current_user()
            row_id = db.save_calculation(
                inputs_to_save, outputs_to_save, note,
                user_id=current_user["id"] if current_user else None
            )
            st.success(f"Calculation saved — Record ID #{row_id}")
        except Exception as e:
            st.error(f"Could not save: {e}")

    # Save Template — outside if calc_clicked so it persists
    if "last_inputs" in st.session_state:
        st.markdown("---")
        with st.container(border=True):
            st.markdown('<div class="section-title">Save as Product Template</div>',
                        unsafe_allow_html=True)
            st.markdown(
                '<div class="info-box">Save all current inputs as a reusable template. '
                'Saving with the same name updates the existing one.</div>',
                unsafe_allow_html=True,
            )
            tpl_name_default = (
                st.session_state["last_inputs"].get("product_name", "").strip()
                or st.session_state["last_inputs"].get("pc_name", "").strip()
                or "My Product"
            )
            sv1, sv2 = st.columns([2, 1])
            with sv1:
                tpl_name = st.text_input(
                    "Template name",
                    value=tpl_name_default,
                    placeholder="e.g. Compressor GA45",
                    key="save_tpl_name",
                )
            with sv2:
                st.markdown("<div style='margin-top:26px'></div>", unsafe_allow_html=True)
                save_tpl = st.button("Save Template", key="save_tpl_btn")

            if save_tpl:
                ok_save, save_msg = pm.save_product(tpl_name, st.session_state["last_inputs"])
                if ok_save:
                    st.toast(f"✓ {save_msg}", icon="✅")
                else:
                    st.toast(f"✗ {save_msg}", icon="❌")


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 2 — MY CALCULATIONS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "My Calculations":
    st.markdown(
        '<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.2rem;'
        'font-weight:700;color:#003057;text-transform:uppercase;letter-spacing:1.5px;'
        'margin-bottom:14px;">My Calculations — Saved Records</div>',
        unsafe_allow_html=True
    )

    current_user = auth_session.current_user()

    if not current_user:
        st.markdown(
            '<div class="info-box">Please <b>Sign In</b> (top right) to view your saved calculations.</div>',
            unsafe_allow_html=True,
        )
        if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_ID != "your_client_id_here":
            _, gate_col, _ = st.columns([2, 1, 2])
            with gate_col:
                render_signin_link(GOOGLE_CLIENT_ID, GOOGLE_REDIRECT_URI, label="Sign in with Google")
        records = None

    else:
        records = db.get_all_calculations(user_id=current_user["id"])

    if records is None:
        pass
    elif not records:
        st.markdown("""<div class="info-box" style="text-align:center;padding:32px;">
            <div style="font-size:1.2rem;font-weight:700;color:#003057;margin-bottom:6px;">
                No records yet
            </div>
            <div style="color:#8D9BAD;font-size:0.85rem;">
                Run a calculation — it saves automatically after clicking CALCULATE.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="color:#8D9BAD;font-size:0.82rem;margin-bottom:10px;">'
            f'{len(records)} record(s) found</div>',
            unsafe_allow_html=True
        )

        table_rows = []
        for r in records:
            inp = r.get("inputs", {})
            out = r.get("outputs", {})
            ts  = str(r.get("timestamp", ""))
            try:
                dt       = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%d %b %Y")
                time_str = dt.strftime("%H:%M")
            except Exception:
                date_str = ts[:10]
                time_str = ts[11:16]
            table_rows.append({
                "ID":           r.get("id"),
                "Date":         date_str,
                "Time":         time_str,
                "Project":      inp.get("pc_name", "—"),
                "Product":      inp.get("product_name", "—"),
                "L×W×H (mm)":  (f"{inp.get('length_mm',0):.0f}×"
                                 f"{inp.get('width_mm',0):.0f}×"
                                 f"{inp.get('height_mm',0):.0f}"),
                "Box":          inp.get("box_choice", "—"),
                "Corr Wt (kg)":   round(out.get("corr_weight_kg", 0), 3),
                "Wood Wt (kg)":   round(out.get("wood_weight_kg", 0), 3),
                "Pallet Wt (kg)": round(out.get("pallet_wt_kg", 0), 3),
                "CO₂ Design":     round(out.get("co2_total_design", 0), 4),
                "CO₂ Physical":   round(out.get("co2_total_phys", 0), 4),
                "Transport":      inp.get("transport_design", "—"),
                "Notes":          r.get("description", ""),
            })

        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True, hide_index=True,
                     column_config={
                         "CO₂ Design":   st.column_config.NumberColumn("CO₂ Design (kg)",   format="%.4f"),
                         "CO₂ Physical": st.column_config.NumberColumn("CO₂ Physical (kg)", format="%.4f"),
                     })

        st.markdown("---")
        with st.container(border=True):
            st.markdown('<div class="section-title">Record Actions</div>', unsafe_allow_html=True)
            ids    = [r.get("id") for r in records]
            del_id = st.selectbox("Select Record ID to Delete", ids, key="del_sel")
            if st.button("Delete Selected Record"):
                db.delete_calculation(del_id)
                st.success(f"Record #{del_id} deleted.")
                st.rerun()

            sel_id  = st.selectbox("Select Record ID to Inspect", ids, key="inspect_id")
            sel_rec = next((r for r in records if r.get("id") == sel_id), None)
            if sel_rec:
                with st.expander(f"Full Detail — Record #{sel_id}", expanded=False):
                    ic, oc = st.columns(2)
                    with ic:
                        st.markdown("**Inputs**")
                        st.json(sel_rec.get("inputs", {}))
                    with oc:
                        st.markdown("**Outputs**")
                        st.json(sel_rec.get("outputs", {}))
                    if sel_rec.get("description"):
                        st.markdown(f"**Notes:** {sel_rec['description']}")

        if len(records) >= 25:
            st.markdown("---")
            with st.expander("📊 Statistics", expanded=False):
                co2_vals = [r.get("outputs", {}).get("co2_total_design", 0) for r in records]
                st.markdown(
                    f'<div style="color:#8D9BAD;font-size:0.82rem;margin-bottom:10px;">'
                    f'Based on Design Calculation CO₂ across {len(records)} saved calculation(s)</div>',
                    unsafe_allow_html=True
                )
                s1, s2, s3, s4 = st.columns(4)
                with s1:
                    st.markdown(f"""<div class="metric-card">
                        <div class="m-label">Total Calculations</div>
                        <div class="m-value">{len(co2_vals)}</div></div>""", unsafe_allow_html=True)
                with s2:
                    st.markdown(f"""<div class="metric-card">
                        <div class="m-label">Average CO₂</div>
                        <div class="m-value">{sum(co2_vals) / len(co2_vals):.4f}</div>
                        <div class="m-unit">kg CO₂</div></div>""", unsafe_allow_html=True)
                with s3:
                    st.markdown(f"""<div class="metric-card">
                        <div class="m-label">Lowest CO₂</div>
                        <div class="m-value">{min(co2_vals):.4f}</div>
                        <div class="m-unit">kg CO₂</div></div>""", unsafe_allow_html=True)
                with s4:
                    st.markdown(f"""<div class="metric-card">
                        <div class="m-label">Highest CO₂</div>
                        <div class="m-value">{max(co2_vals):.4f}</div>
                        <div class="m-unit">kg CO₂</div></div>""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 3 — PRODUCT CATALOG
# ═════════════════════════════════════════════════════════════════════════════
elif page == "Product Catalog":
    st.markdown(
        '<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.2rem;'
        'font-weight:700;color:#003057;text-transform:uppercase;letter-spacing:1.5px;'
        'margin-bottom:14px;">Product Catalog — Saved Templates</div>',
        unsafe_allow_html=True
    )

    products = pm.list_products()

    if not products:
        st.markdown("""<div class="info-box" style="text-align:center;padding:32px;">
            <div style="font-size:1.2rem;font-weight:700;color:#003057;margin-bottom:6px;">
                No product templates yet
            </div>
            <div style="color:#8D9BAD;font-size:0.85rem;">
                Run a calculation and use <b>Save as Product Template</b> to add products here.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div style="color:#8D9BAD;font-size:0.82rem;margin-bottom:10px;">'
            f'{len(products)} product(s) saved</div>',
            unsafe_allow_html=True
        )
        df_prod = pd.DataFrame([{
            "Name":         p["name"],
            "PC / Code":    p["pc_name"] or "—",
            "Last Updated": p["updated_at"],
        } for p in products])
        st.dataframe(df_prod, use_container_width=True, hide_index=True)

        st.markdown("---")

        if not auth_session.is_admin():
            st.markdown(
                '<div class="info-box">Inspecting, deleting, and renaming templates is '
                'restricted to admins.</div>',
                unsafe_allow_html=True,
            )
        else:
            with st.container(border=True):
                st.markdown('<div class="section-title">Inspect / Delete</div>', unsafe_allow_html=True)
                prod_names = [p["name"] for p in products]
                sel_prod   = st.selectbox("Select product", prod_names, key="cat_sel")

                ia, da = st.columns(2)
                with ia:
                    if st.button("Inspect Selected", key="inspect_prod"):
                        data = pm.load_product(sel_prod)
                        if data:
                            with st.expander(f"Fields — {sel_prod}", expanded=True):
                                st.json(data)
                with da:
                    if st.button("Delete Selected", key="del_prod"):
                        ok_del, del_msg = pm.delete_product(sel_prod)
                        if ok_del:
                            st.success(del_msg)
                            st.rerun()
                        else:
                            st.error(del_msg)

            with st.container(border=True):
                st.markdown('<div class="section-title">Rename Product</div>', unsafe_allow_html=True)
                rn1, rn2, rn3 = st.columns([2, 2, 1])
                with rn1:
                    rn_old = st.selectbox("Product to rename", prod_names, key="rn_old")
                with rn2:
                    rn_new = st.text_input("New name", placeholder="New template name", key="rn_new")
                with rn3:
                    st.markdown("<div style='margin-top:26px'></div>", unsafe_allow_html=True)
                    if st.button("Rename", key="rn_btn"):
                        ok_rn, rn_msg = pm.rename_product(rn_old, rn_new)
                        if ok_rn:
                            st.success(rn_msg)
                            st.rerun()
                        else:
                            st.error(rn_msg)


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 4 — SETTINGS
# ═════════════════════════════════════════════════════════════════════════════
elif page == "Settings":
    st.markdown(
        '<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.2rem;'
        'font-weight:700;color:#003057;text-transform:uppercase;letter-spacing:1.5px;'
        'margin-bottom:14px;">Settings &amp; Reference Data</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):
        st.markdown('<div class="section-title">Database Connection</div>', unsafe_allow_html=True)
        ok, msg = db.test_connection()
        if ok:
            st.success(f"Connected — {msg}")
        else:
            st.warning(f"Not connected — {msg}")
        st.markdown(
            '<div class="info-box">To use MySQL, set <b>use_mysql: True</b> in '
            '<code>config/settings.py</code> with your credentials.</div>',
            unsafe_allow_html=True
        )

    with st.container(border=True):
        st.markdown('<div class="section-title">Automatic Distance — OpenRouteService</div>',
                    unsafe_allow_html=True)
        if ORS_API_KEY:
            st.success("API key configured — automatic distance calculation is active.")
        else:
            st.warning("No API key set — distance must be entered manually.")
        st.markdown("""
        <div class="info-box">
        <b>How to get a free OpenRouteService API key:</b><br>
        1. Go to <a href="https://openrouteservice.org/dev/#/signup" target="_blank">openrouteservice.org/dev/#/signup</a><br>
        2. Register with an email address (free, no credit card)<br>
        3. Dashboard → Tokens → <b>CREATE TOKEN</b> → copy the key<br>
        4. Paste into <code>config/settings.py</code>: <code>ORS_API_KEY = "your_key"</code><br>
        Free tier: <b>2,000 requests/day</b>
        </div>
        """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="section-title">Google OAuth</div>', unsafe_allow_html=True)
        if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_ID != "your_client_id_here":
            st.success("Google OAuth configured — login is active.")
        else:
            st.warning("Google OAuth not configured — add credentials to config/settings.py.")

    with st.container(border=True):
        st.markdown('<div class="section-title">Emission Factors Reference</div>', unsafe_allow_html=True)
        ef1, ef2, ef3 = st.columns(3)
        with ef1:
            st.markdown("**Material (kgCO₂/kg)**")
            st.dataframe(pd.DataFrame({
                "Material": list(EMISSION_FACTORS.keys()),
                "kgCO₂/kg": list(EMISSION_FACTORS.values())
            }), hide_index=True)
        with ef2:
            st.markdown("**Plastics (kgCO₂/kg)**")
            st.dataframe(pd.DataFrame({
                "Plastic":  list(PLASTIC_EMISSION_FACTORS.keys()),
                "kgCO₂/kg": list(PLASTIC_EMISSION_FACTORS.values())
            }), hide_index=True)
        with ef3:
            st.markdown("**Transport (kgCO₂/tonne·km)**")
            st.dataframe(pd.DataFrame({
                "Mode":       list(TRANSPORT_FACTORS.keys()),
                "kgCO₂/t·km": [round(v, 4) for v in TRANSPORT_FACTORS.values()]
            }), hide_index=True)

    with st.container(border=True):
        st.markdown('<div class="section-title">Excel Cell Mapping</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame({
            "Excel Cell": ["E12/G12/H12","E16/G16/H16","B16","M16","N16",
                           "B19","I19","M19","N19","K22","M22","N22",
                           "E30","H30","K30","Backup!H32","Backup!H38"],
            "Python Function": [
                "Input dims","corrugated_adjusted_dims()","ply input",
                "corrugated_box_area()","corrugated_box_weight()",
                "thickness_mm","wood_type_box","wooden_box_volume()",
                "wooden_box_weight()","wood_type_pallet","pallet_volume()",
                "pallet_weight()","material_co2_corrugated()",
                "material_co2_wooden_box()","material_co2_pallet()",
                "transport_co2_design()","transport_co2_physical()"],
            "Description": [
                "Product L×W×H mm","+40mm clearance applied","3/5/7 ply selection",
                "Ply-adjusted area m²","Weight with ply density factor",
                "Wall thickness mm","Solidwood or Plywood",
                "Hollow box net volume m³","×600 kg/m³",
                "Pallet wood type","Deck+Runner+Plank volume m³","×500 kg/m³",
                "wt×0.491","wt×wood factor","wt×pallet factor",
                "dist×(kg/1000)×transport_factor","Same, physical path"],
        }), use_container_width=True, hide_index=True)