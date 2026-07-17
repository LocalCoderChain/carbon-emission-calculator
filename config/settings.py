"""
config/settings.py — Application configuration
================================================
Secrets (API keys, OAuth credentials, DB password) are read from environment
variables — see .env.example for the expected keys. Create a local .env file
(gitignored) with real values; python-dotenv loads it automatically below.
"""

import os
from dotenv import load_dotenv

load_dotenv()

APP_TITLE   = "Carbon Emission Calculator"
APP_VERSION = "1.2.0"
BRAND       = "Atlas Copco"

# ── Database ──────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "use_mysql":   os.environ.get("DB_USE_MYSQL", "false").lower() == "true",
    "sqlite_path": "carbon_calculator.db",         # SQLite file path
    # MySQL settings (only used when use_mysql=True)
    "host":     os.environ.get("DB_HOST", "localhost"),
    "port":     int(os.environ.get("DB_PORT", "3306")),
    "database": os.environ.get("DB_NAME", "carbon_db"),
    "user":     os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
}

# ── OpenRouteService API (automatic distance calculation) ─────────────────────
# Free tier — 2,000 requests/day, no credit card required.
#
# How to get your free API key:
#   1. Go to https://openrouteservice.org/dev/#/signup
#   2. Register with an email address (free)
#   3. After confirming your email, log in and go to Dashboard → Tokens
#   4. Click "CREATE TOKEN" → give it any name → copy the key
#   5. Paste it below (replace the empty string)
#
# Leave as "" to disable automatic distance — manual entry stays fully functional.
ORS_API_KEY = os.environ.get("ORS_API_KEY", "")

GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "your_client_id_here")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI  = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:8501")
ADMIN_EMAILS         = [e.strip() for e in os.environ.get("ADMIN_EMAILS", "").split(",") if e.strip()]
