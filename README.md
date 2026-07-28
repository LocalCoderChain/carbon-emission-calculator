# Carbon Emission Calculator

A full-stack Streamlit application for estimating carbon emissions generated from packaging materials and transportation methods — built for Atlas Copco-style packaging workflows, with Google SSO, role-based admin tooling, and automatic distance calculation.

The tool lets users model a shipment's packaging (corrugated box, wooden box, wooden pallet) two ways — a **Design Calculation** from product dimensions, or a **Physical Input** from measured weights — estimate CO₂ emissions across materials and transport, compare the two paths, and store historical calculations for later analysis.

---

## Key Highlights

* **Authentication & Authorization** — Google OAuth 2.0 login with a database-backed session layer and role-based access control (admin vs. standard user)
* **Admin Dashboard** — user management, live-editable emission/transport factors, active session control, and soft-delete/restore for calculation records
* **External API Integration** — automatic road/rail/sea/air distance lookups via the OpenRouteService geocoding + routing APIs
* **Secure Configuration** — all API keys, OAuth credentials, and DB credentials are read from environment variables (`.env`), never hardcoded
* **Data Integrity** — soft-delete pattern for calculation records (users can delete their own records; admins retain full visibility and can restore them)
* **Interactive Calculation Grid** — a live, per-component pallet breakdown (Deck / Runner-Block / Plank-Runner) with editable dimensions and wood type per row, weight recalculating in real time

---

## Features

**Calculation Engine**
* Packaging weight estimation from product dimensions (corrugated box, wooden box, wooden pallet)
* Per-component pallet breakdown — Deck, Runner/Block, and Plank/Runner each with independently editable dimensions, count, and wood type; weight and CO₂ recompute live
* FEFCO box style selection (201 / 200 / 310) for corrugated boxes — recorded per calculation for reporting; not yet factored into the weight formula
* Carbon emission calculations for packaging materials and 5 plastic subtypes
* Transport emission calculations for Road, Rail, Sea, and Air
* Side-by-side comparison of Design Calculation vs. Physical Input paths

**Authentication & Access Control**
* Google SSO login (OAuth 2.0), with CSRF-protected state handling
* Persistent, database-backed sessions that survive a page refresh
* Role-based access: only admins can inspect/rename/delete product templates or manage other users
* Admin dashboard: user role management, all-calculations oversight with per-user filtering and soft-delete/restore, active session monitoring/revocation, and live emission/transport/pallet-constant configuration

**Data & History**
* Historical calculation storage (SQLite by default, optional MySQL)
* Per-user "My Calculations" view, gated behind login
* Soft-delete for calculation records — hidden from the user, recoverable by an admin
* A statistics panel (average / lowest / highest CO₂) once a user has 25+ saved calculations
* Reusable product templates — save, load, rename, and delete full input sets

**Distance & Transport**
* Automatic road/rail distance and straight-line air/sea distance via OpenRouteService
* Manual distance entry fallback if no API key is configured

---

## Technology Stack

| Technology | Purpose |
| ---------- | ------- |
| Python | Core application logic |
| Streamlit | User interface |
| SQLite / MySQL | Data storage (configurable) |
| Pandas | Data handling |
| requests / requests-oauthlib | Google OAuth 2.0 flow, OpenRouteService API calls |
| python-dotenv | Environment-variable based secrets management |
| OpenRouteService API | Geocoding + routing for automatic distance calculation |

---

## Project Structure

```text
carbon_calculator_github/
│
├── app.py                    # Main Streamlit app — UI, routing, calculation orchestration
├── requirements.txt
├── README.md
├── .env.example               # Template for required environment variables
│
├── auth/
│   ├── google_oauth.py        # Google OAuth 2.0 flow
│   └── session.py             # Login/session state helpers
├── auth_pages/
│   ├── login.py                # Login page + OAuth callback handling
│   └── admin.py                 # Admin dashboard
├── config/
│   └── settings.py              # App config, loaded from environment variables
├── database/
│   └── db.py                    # DatabaseManager, ProductManager, UserManager, ConfigManager, SessionManager, OAuthStateManager
├── utils/
│   ├── formulas.py               # Emission/weight calculation engine
│   └── distance.py                # OpenRouteService geocoding + routing
├── assets/
├── docs/
└── screenshots/
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/LocalCoderChain/carbon-emission-calculator.git
cd carbon-emission-calculator
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```
(or run `SETUP.bat`)

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in your own values:

```bash
# Windows (Command Prompt)
copy .env.example .env

# macOS / Linux / Git Bash
cp .env.example .env
```

| Variable | Required? | Notes |
| -------- | --------- | ----- |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Optional | From a Google Cloud OAuth 2.0 Client ID — needed for login. App runs without it, just without SSO. |
| `GOOGLE_REDIRECT_URI` | Optional | Defaults to `http://localhost:8501` |
| `ORS_API_KEY` | Optional | Free key from [openrouteservice.org](https://openrouteservice.org/dev/#/signup) — needed for automatic distance calculation. Manual distance entry works without it. |
| `ADMIN_EMAILS` | Optional | Comma-separated list of emails granted admin role on first login |
| `DB_*` | Optional | Only needed if using MySQL instead of the SQLite default |

### 4. Run the application

```bash
streamlit run app.py
```
(or click `StartTheApp.bat`)

The app opens automatically in your browser.

---

## Database

SQLite is used by default and created automatically on first launch — zero setup required. MySQL is supported as a drop-in alternative via the `.env` configuration.

---

## Sample Functionality

The application can calculate:

* Corrugated box weight and area
* Wooden box weight and volume
* Per-component wooden pallet weight (Deck / Runner-Block / Plank-Runner)
* Packaging material emissions (corrugated, wood, plastic — 5 subtypes)
* Transportation emissions across Road, Rail, Sea, and Air
* Total carbon footprint, compared across Design vs. Physical input methods

---

## Validation

The calculation engine was verified against reference spreadsheet calculations to ensure consistency and accuracy.

Example validation case:

| Output | Value |
| ------ | ----- |
| Corrugated Box Area | 2.724960 m² |
| Corrugated Box Weight | 2.861208 kg |
| Wooden Box Weight | 7.449600 kg |
| Pallet Weight | 11.825550 kg |
| Transport CO₂ (Air, 1000 km) | 15.058922 kg |

---

## Screenshots

Screenshots live in the `screenshots/` directory. Current set covers the calculator, database, and settings views — a refreshed set covering the newer features is planned, including:

* Google Sign-In flow
* Calculator with the pallet component grid
* Admin dashboard (user management, live config, active sessions)
* My Calculations page with the statistics panel
* Product Catalog (template save/load)

---

## Future Improvements

* Deploy to a live hosted instance (Render)
* Export reports to PDF and Excel
* Automated test suite (pytest)
* Enhanced analytics dashboard with charts
* Performance optimizations for larger datasets

---

## Author

**Arya Barsode**
Pune, Maharashtra, India

[GitHub](https://github.com/localcoderchain) · [LinkedIn](https://linkedin.com/in/aryabarsode) · aryabarsodae@gmail.com
