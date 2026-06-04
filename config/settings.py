"""
config/settings.py
==================
Application configuration. Edit DB_CONFIG to connect to MySQL.
"""

import os

# ── DATABASE CONFIGURATION ────────────────────────────────────────────────────
# Set use_mysql=True and fill in credentials to use MySQL.
# When use_mysql=False (default), the app uses SQLite stored in the user's
# home directory — zero setup required for end users.
DB_CONFIG = {
    "use_mysql":  False,            # ← Set True to use MySQL
    "host":       "localhost",
    "port":       3306,
    "user":       "root",
    "password":   "",               # ← Fill in MySQL password
    "database":   "carbon_calculator",
    "sqlite_path": os.path.join(
        os.path.expanduser("~"),
        "carbon_calculator.db"
    ),
}

# ── APP METADATA ──────────────────────────────────────────────────────────────
APP_TITLE   = "Carbon Emission Calculator"
APP_VERSION = "1.0.0"
COMPANY     = "Atlas Copco"

# ── ATLAS COPCO BRAND COLOURS ─────────────────────────────────────────────────
BRAND = {
    "primary":      "#00AEEF",   # Atlas Copco cyan/blue
    "dark":         "#003057",   # Deep navy
    "white":        "#FFFFFF",
    "light_grey":   "#F4F6F8",
    "mid_grey":     "#8D9BAD",
    "text":         "#1A2B3C",
    "success":      "#00A878",
    "warning":      "#F5A623",
    "danger":       "#E53935",
    "card_bg":      "#FFFFFF",
    "sidebar_bg":   "#003057",
    "sidebar_text": "#FFFFFF",
}
