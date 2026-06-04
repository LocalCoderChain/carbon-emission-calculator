"""
app.py — Carbon Emission Calculator
Atlas Copco | Streamlit UI
"""

import sys, os

if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

import streamlit as st
import pandas as pd
from datetime import datetime

from utils.formulas import (
    calculate_all,
    TRANSPORT_FACTORS,
    PLASTIC_EMISSION_FACTORS,
    EMISSION_FACTORS,
    BOX_CLEARANCE,
)
from database.db import DatabaseManager
from config.settings import DB_CONFIG, APP_TITLE, APP_VERSION, BRAND

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# CHANGE 1: no emoji page_icon, clean title
# ─────────────────────────────────────────────────────────────────────────────
st.write("Loading...")
st.set_page_config(
    page_title="Carbon Emission Calculator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS — unchanged from original, just kept as-is
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
    text-transform: uppercase;
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
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    return DatabaseManager(DB_CONFIG)

db = get_db()


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# CHANGE 1: no emojis in nav items
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
    page = st.radio(
        "Navigation",
        ["Calculate Carbon Emissions", "My Calculations", "Settings"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    ok, msg = db.test_connection()
    if ok:
        st.markdown('<div style="font-size:0.72rem;color:#00A878;">◆ &nbsp;Database Connected</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:0.72rem;color:#F5A623;">◆ &nbsp;SQLite (local)</div>',
                    unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top:32px;font-size:0.68rem;color:#4A6277;text-align:center;
                border-top:1px solid rgba(0,174,239,0.2);padding-top:12px;">
        v{APP_VERSION} &nbsp;·&nbsp; Atlas Copco Confidential
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# CHANGE 1: no emoji, clean title "Calculate Carbon Emissions"
# ─────────────────────────────────────────────────────────────────────────────
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


# ═════════════════════════════════════════════════════════════════════════════
# PAGE 1 — CALCULATOR
# CHANGE 2: st.container(border=True) instead of st.markdown('<div class="section-card">') 
#           This removes the ghost/empty white boxes
# CHANGE 3: Radio button replaces dual checkboxes for box type
#           Only the active box type contributes to CO2 (matches Excel logic)
# ═════════════════════════════════════════════════════════════════════════════
if page == "Calculate Carbon Emissions":

    # ── Identity ──────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown('<div class="section-title">Project Identity</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            pc_name = st.text_input("PC / Production Center", value="", placeholder="e.g. ABC-2024")
        with c2:
            product_name = st.text_input("Product Name", value="", placeholder="e.g. Compressor GA45")
        with c3:
            business_area = st.selectbox(
                "Business Area",
                ["CTBN (Compressor Technique Business Area)", "VTBN (Vacuum Technique Business Area)", "PTBA (Power Technique Business Area)", "ITBA (Industrial Technique Business Area)"],
                index=0
            )

    # ── Two-column layout ─────────────────────────────────────────────────
    left_col, right_col = st.columns([1, 1], gap="large")

    # ══════════════════════════════════════════
    # LEFT — DESIGN CALCULATION
    # ══════════════════════════════════════════
    with left_col:
        with st.container(border=True):
            st.markdown(
                '<div class="section-title">Design Calculation'
                '<span style="font-size:0.7rem;font-weight:400;color:#8D9BAD;'
                'margin-left:10px;text-transform:none;letter-spacing:0">'
                "If you don't know the weight of your packaging material</span></div>",
                unsafe_allow_html=True
            )

            # Product Dimensions
            st.markdown('<div class="sub-section-title">Product Size (mm)</div>', unsafe_allow_html=True)
            d1, d2, d3 = st.columns(3)
            with d1:
                length_mm = st.number_input("Length", min_value=0.0, value=600.0, step=10.0, format="%.1f")
            with d2:
                width_mm  = st.number_input("Width",  min_value=0.0, value=400.0, step=10.0, format="%.1f")
            with d3:
                height_mm = st.number_input("Height", min_value=0.0, value=300.0, step=10.0, format="%.1f")

            st.markdown(
                f'<div class="info-box">+{BOX_CLEARANCE} mm clearance added automatically '
                f'to each dimension so the box fits safely around the product. (Excel: E12+40)</div>',
                unsafe_allow_html=True
            )

            st.markdown("---")

            # ── CHANGE 3: Radio replaces dual checkboxes ──────────────────
            # Excel has M12 (corrugated) and M13 (wooden) as separate checkboxes
            # but only ONE should drive the CO2 calculation at a time.
            # A radio button correctly enforces this mutual exclusivity.
            st.markdown('<div class="sub-section-title">Box Type</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="info-box">Select ONE box type — corrugated and wooden box '
                'are alternatives. The chosen box sits on top of the pallet.</div>',
                unsafe_allow_html=True
            )
            box_choice = st.radio(
                "Box Type",
                ["Corrugated Box", "Wooden Box"],
                index=0,
                horizontal=True,
                label_visibility="collapsed",
                key="box_choice"
            )
            use_corrugated = (box_choice == "Corrugated Box")
            use_wooden     = (box_choice == "Wooden Box")

            # Corrugated Box fields — Excel B15/B16 (ply)
            # Only shown when Corrugated Box is selected
            if use_corrugated:
                ply = st.selectbox("Box Ply", [3, 5, 7], index=1)
            else:
                ply = 5  # not used for wooden box

            # Excel B18/B19 — Box Thickness and Wood Type
            # These are ALWAYS shown regardless of box type (separate rows in Excel)
            # Thickness feeds into wooden box volume formula M19
            # Wood Type feeds into CO2 emission factor lookup
            if use_wooden:
                st.markdown('<div class="sub-section-title">Wooden Box Properties</div>',
                        unsafe_allow_html=True)
                bw1, bw2 = st.columns(2)
                with bw1:
                    thickness_mm = st.number_input(
                        "Box Thickness (mm)", 
                        min_value=1.0, value=20.0, step=1.0, format="%.0f"
                        )
                    with bw2:
                        wood_type_box = st.selectbox(
                            "Wood Type (Box)", ["Solidwood", "Plywood"], key="wt_box"
                            )
            else:
                thickness_mm=20.0
                wood_type_box="Solidwood"
        

            st.markdown("---")

            # Wooden Pallet
            st.markdown('<div class="sub-section-title">Wooden Pallet</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="info-box">Pallet dimensions auto-calculated from product size. '
                'Fixed: Deck H=36mm · Runner 125×110×90mm (×9) · Planks W×90×20mm (×3)</div>',
                unsafe_allow_html=True
            )
            wood_type_pallet = st.selectbox("Wood Type (Pallet)", ["Plywood", "Solidwood"], key="wt_pallet")

            st.markdown("---")

            # Transportation — Design
            st.markdown('<div class="sub-section-title">Transportation</div>', unsafe_allow_html=True)
            transport_design = st.selectbox(
                "Transport Type", list(TRANSPORT_FACTORS.keys()), index=0, key="trans_design"
            )
            t1, t2 = st.columns(2)
            with t1:
                product_weight_kg = st.number_input(
                    "Product Weight (kg)", min_value=0.0, value=10.0, step=0.5, format="%.1f"
                )
            with t2:
                distance_design_km = st.number_input(
                    "Distance (km)", min_value=0.0, value=1000.0, step=50.0, format="%.0f"
                )

    # ══════════════════════════════════════════
    # RIGHT — PHYSICAL INPUT
    # ══════════════════════════════════════════
    with right_col:
        with st.container(border=True):
            st.markdown(
                '<div class="section-title">Physical Input'
                '<span style="font-size:0.7rem;font-weight:400;color:#8D9BAD;'
                'margin-left:10px;text-transform:none;letter-spacing:0">'
                "If you know the weight of your packaging material</span></div>",
                unsafe_allow_html=True
            )

            # Material Weights (Excel U12, U13, U14, U15)
            st.markdown('<div class="sub-section-title">Material Weights (kg)</div>', unsafe_allow_html=True)
            p1, p2 = st.columns(2)
            with p1:
                phys_corrugated_kg = st.number_input(
                    "Corrugated Box (kg)", min_value=0.0, value=0.0,
                    step=0.1, key="phys_corr", format="%.3f"
                )
                phys_wooden_kg = st.number_input(
                    "Wooden Box (kg)", min_value=0.0, value=0.0,
                    step=0.1, key="phys_wood", format="%.3f"
                )
            with p2:
                phys_pallet_kg = st.number_input(
                    "Wooden Pallet (kg)", min_value=0.0, value=0.0,
                    step=0.1, key="phys_pallet", format="%.3f"
                )
                phys_plastic_kg = st.number_input(
                    "Plastic Material (kg)", min_value=0.0, value=0.0,
                    step=0.1, key="phys_plastic", format="%.3f"
                )

            # Plastic Type (Excel T25)
            st.markdown('<div class="sub-section-title">Plastic Type</div>', unsafe_allow_html=True)
            phys_plastic_type = st.selectbox(
                "Plastic Type", list(PLASTIC_EMISSION_FACTORS.keys()), key="phys_ptype"
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
            # Wood Type — Physical Input (Excel: Packaging Material > Wood > Wood Type dropdown)
            st.markdown('<div class="sub-section-title">Wood Type (Physical)</div>', unsafe_allow_html=True)
            phys_wood_type = st.selectbox(
                "Wood Type (Physical)", ["Solidwood", "Plywood"], key="phys_wt"
                )
            st.markdown(
                '<div class="info-box">Select the wood type for your physical wooden box and pallet. '
                'Used to determine CO₂ emission factor: Solidwood = 0.31 kgCO₂/kg · Plywood = 0.68 kgCO₂/kg</div>',
                unsafe_allow_html=True
                )

            st.markdown("---")

            # Packaging Combination (Excel S18/S19)
            st.markdown('<div class="sub-section-title">Packaging Combination (for Transport)</div>',
                        unsafe_allow_html=True)
            st.markdown(
                '<div class="info-box">Which box type is being shipped on the pallet? '
                'Sets the combined weight for transport CO₂. (Excel S18/S19)</div>',
                unsafe_allow_html=True
            )
            phys_pkg_combo = st.radio(
                "Packaging combination",
                ["corrugated+pallet", "wooden+pallet"],
                format_func=lambda x: "Corrugated Box + Pallet" if x == "corrugated+pallet"
                                      else "Wooden Box + Pallet",
                key="phys_combo",
                label_visibility="collapsed"
            )

            st.markdown("---")

            # Transportation — Physical (Excel P34, T34, W34)
            st.markdown('<div class="sub-section-title">Transportation</div>', unsafe_allow_html=True)
            transport_physical = st.selectbox(
                "Transport Type", list(TRANSPORT_FACTORS.keys()), index=0, key="trans_phys"
            )
            p3, p4 = st.columns(2)
            with p3:
                phys_product_weight_kg = st.number_input(
                    "Product Weight (kg)", min_value=0.0, value=0.0,
                    step=0.5, key="phys_prod_wt", format="%.1f"
                )
            with p4:
                distance_physical_km = st.number_input(
                    "Distance (km)", min_value=0.0, value=1000.0,
                    step=50.0, key="dist_phys", format="%.0f"
                )

    # ── Notes ─────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown('<div class="section-title">Notes / Description</div>', unsafe_allow_html=True)
        note = st.text_area(
            "Add a note for this calculation",
            placeholder="e.g. Shipment from Pune to Frankfurt, Q1 2025...",
            height=80, label_visibility="collapsed"
        )

    # ── Calculate button ───────────────────────────────────────────────────
    _, btn_col, _ = st.columns([2, 1, 2])
    with btn_col:
        calc_clicked = st.button("CALCULATE", use_container_width=True)

    # ── Results ────────────────────────────────────────────────────────────
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

        st.markdown("---")
        st.markdown(
            '<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.2rem;'
            'font-weight:700;color:#003057;text-transform:uppercase;letter-spacing:1.5px;'
            'margin-bottom:14px;">Calculation Results</div>',
            unsafe_allow_html=True
        )

        res_left, res_right = st.columns(2, gap="large")

        # Design outputs
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

        # Physical outputs
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

        # Sustainability comparison
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

        # Save to DB
        inputs_to_save = {
            "pc_name": pc_name, "product_name": product_name,
            "business_area": business_area,
            "length_mm": length_mm, "width_mm": width_mm, "height_mm": height_mm,
            "box_choice": box_choice, "ply": ply, "thickness_mm": thickness_mm,
            "wood_type_box": wood_type_box, "wood_type_pallet": wood_type_pallet,
            "transport_design": transport_design,
            "product_weight_kg": product_weight_kg,
            "distance_design_km": distance_design_km,
            "phys_corrugated_kg": phys_corrugated_kg,
            "phys_wooden_kg": phys_wooden_kg,
            "phys_pallet_kg": phys_pallet_kg,
            "phys_plastic_kg": phys_plastic_kg,
            "phys_plastic_type": phys_plastic_type,
            "phys_pkg_combo": phys_pkg_combo,
            "transport_physical": transport_physical,
            "phys_product_weight_kg": phys_product_weight_kg,
            "distance_physical_km": distance_physical_km,
        }
        outputs_to_save = {k: round(v, 6) if isinstance(v, float) else v
                           for k, v in results.items()}
        try:
            row_id = db.save_calculation(inputs_to_save, outputs_to_save, note)
            st.success(f"Calculation saved — Record ID #{row_id}")
        except Exception as e:
            st.error(f"Could not save: {e}")


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

    records = db.get_all_calculations()

    if not records:
        st.markdown("""<div class="info-box" style="text-align:center;padding:32px;">
            <div style="font-size:1.2rem;font-weight:700;color:#003057;margin-bottom:6px;">
                No records yet
            </div>
            <div style="color:#8D9BAD;font-size:0.85rem;">
                Run a calculation — it saves automatically after clicking CALCULATE.
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        # ── Build full table first ────────────────────────────────────────
        table_rows = []
        for r in records:
            inp = r.get("inputs", {}); out = r.get("outputs", {}); ts = str(r.get("timestamp", ""))
            try:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%d %b %Y"); time_str = dt.strftime("%H:%M")
                month_num = dt.month; year_num = dt.year
            except Exception:
                date_str = ts[:10]; time_str = ts[11:16]
                month_num = 0; year_num = 0
            table_rows.append({
                "ID":             r.get("id"),
                "Date":           date_str,
                "Time":           time_str,
                "_month":         month_num,
                "_year":          year_num,
                "Project":        inp.get("pc_name", "—"),
                "Product":        inp.get("product_name", "—"),
                "Business Area":  inp.get("business_area", "—"),
                "L×W×H (mm)":    (f"{inp.get('length_mm',0):.0f}×"
                                   f"{inp.get('width_mm',0):.0f}×"
                                   f"{inp.get('height_mm',0):.0f}"),
                "Box":            inp.get("box_choice", "—"),
                "Corr Wt (kg)":   round(out.get("corr_weight_kg", 0), 3),
                "Wood Wt (kg)":   round(out.get("wood_weight_kg", 0), 3),
                "Pallet Wt (kg)": round(out.get("pallet_wt_kg", 0), 3),
                "CO₂ Design":     round(out.get("co2_total_design", 0), 4),
                "CO₂ Physical":   round(out.get("co2_total_phys", 0), 4),
                "Transport":      inp.get("transport_design", "—"),
                "Notes":          r.get("description", ""),
            })

        df_full = pd.DataFrame(table_rows)

        # ── FILTERS ──────────────────────────────────────────────────────
        with st.container(border=True):
            st.markdown('<div class="section-title">Filters</div>', unsafe_allow_html=True)
            f1, f2, f3, f4 = st.columns(4)

            with f1:
                all_business_areas = sorted(
                    [x for x in df_full["Business Area"].unique() if x and x != "—"]
                )
                ba_options = ["All"] + all_business_areas
                filter_ba = st.selectbox("Business Area", ba_options, key="filter_ba")

            with f2:
                all_materials = sorted(
                    [x for x in df_full["Box"].unique() if x and x != "—"]
                )
                mat_options = ["All"] + all_materials
                filter_mat = st.selectbox("Box / Material", mat_options, key="filter_mat")

            with f3:
                month_names = {
                    0: "All", 1: "January", 2: "February", 3: "March",
                    4: "April", 5: "May", 6: "June", 7: "July",
                    8: "August", 9: "September", 10: "October",
                    11: "November", 12: "December"
                }
                all_months = sorted(df_full["_month"].unique())
                month_options = [0] + [m for m in all_months if m != 0]
                filter_month = st.selectbox(
                    "Month",
                    month_options,
                    format_func=lambda m: month_names.get(m, str(m)),
                    key="filter_month"
                )

            with f4:
                all_years = sorted(df_full["_year"].unique(), reverse=True)
                year_options = ["All"] + [str(y) for y in all_years if y != 0]
                filter_year = st.selectbox("Year", year_options, key="filter_year")

        # ── Apply filters ─────────────────────────────────────────────────
        df_filtered = df_full.copy()
        if filter_ba != "All":
            df_filtered = df_filtered[df_filtered["Business Area"] == filter_ba]
        if filter_mat != "All":
            df_filtered = df_filtered[df_filtered["Box"] == filter_mat]
        if filter_month != 0:
            df_filtered = df_filtered[df_filtered["_month"] == filter_month]
        if filter_year != "All":
            df_filtered = df_filtered[df_filtered["_year"] == int(filter_year)]

        # Drop internal helper columns before display
        df_display = df_filtered.drop(columns=["_month", "_year"])

        st.markdown(
            f'<div style="color:#8D9BAD;font-size:0.82rem;margin-bottom:10px;">'
            f'{len(df_display)} record(s) shown (of {len(df_full)} total)</div>',
            unsafe_allow_html=True
        )

        st.dataframe(df_display, use_container_width=True, hide_index=True,
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
                        st.markdown("**Inputs**"); st.json(sel_rec.get("inputs", {}))
                    with oc:
                        st.markdown("**Outputs**"); st.json(sel_rec.get("outputs", {}))
                    if sel_rec.get("description"):
                        st.markdown(f"**Notes:** {sel_rec['description']}")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE 3 — SETTINGS
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
            '<code>config/settings.py</code> with your credentials. '
            'By default SQLite is used — no setup needed.</div>',
            unsafe_allow_html=True
        )

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
        st.markdown(
            '<div class="info-box" style="margin-top:10px;">Sources: FEFCO (Corrugated) · '
            'Climatiq (Wood/Plastic) · McKinnon Report (Transport) — '
            'same as Excel Backup calculations sheet.</div>',
            unsafe_allow_html=True
        )

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
