# Carbon Emission Calculator — Packaging & Transport
## Atlas Copco Internal Tool | v1.0.0

---

## 📁 Project Structure

```
carbon_calculator/
├── app.py                  ← Main Streamlit UI (Atlas Copco branded)
├── launcher.py             ← EXE entry point (wraps Streamlit)
├── build.spec              ← PyInstaller build configuration
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
│
├── utils/
│   ├── __init__.py
│   └── formulas.py         ← ALL calculation logic (Excel exact match)
│
├── database/
│   ├── __init__.py
│   └── db.py               ← MySQL + SQLite database handler
│
├── config/
│   ├── __init__.py
│   └── settings.py         ← DB config, brand colours
│
└── assets/                 ← Icons, images (place icon.ico here)
```

---

## 🚀 Quick Start (Developer / IT Setup)

### Step 1 — Install Python 3.10+
Download from https://python.org and check "Add to PATH" during install.

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Run the app
```bash
streamlit run app.py
```
The browser opens at http://localhost:8501 automatically.

---

## 🗄️ Database Setup

### Option A — SQLite (default, zero setup)
- Works out of the box
- Database file stored at: `C:\Users\<YourName>\carbon_calculator.db`
- No MySQL needed; perfect for single-user or testing

### Option B — MySQL (recommended for team use)
1. Install MySQL Server: https://dev.mysql.com/downloads/mysql/
2. Create a user and note credentials
3. Edit `config/settings.py`:
```python
DB_CONFIG = {
    "use_mysql":  True,           # ← Change to True
    "host":       "localhost",
    "port":       3306,
    "user":       "your_user",    # ← Fill in
    "password":   "your_pass",    # ← Fill in
    "database":   "carbon_calculator",  # auto-created
    ...
}
```
4. The app creates the database and table automatically on first run.

**MySQL Table schema:**
```sql
CREATE TABLE calculations (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    input_json  LONGTEXT NOT NULL,
    output_json LONGTEXT NOT NULL,
    description TEXT,
    timestamp   DATETIME NOT NULL
);
```

---

## 📦 Building the EXE (for non-technical users)

### Prerequisites
```bash
pip install pyinstaller
```

### Build command
```bash
cd carbon_calculator
pyinstaller build.spec
```

Output: `dist/CarbonEmissionCalculator.exe`

### Optional — Add custom icon
1. Place `icon.ico` in the `assets/` folder
2. In `build.spec`, uncomment: `icon="assets/icon.ico"`
3. Rebuild

### What happens when user double-clicks EXE
1. App starts a local web server (port 8501)
2. Browser opens automatically at http://localhost:8501
3. Full app is available — no Python, no terminal needed
4. Data saved to SQLite in user's home folder

---

## 🏢 Deploying to Atlas Copco Systems

### Scenario A — Single workstation
1. Copy `dist/CarbonEmissionCalculator.exe` to the target PC
2. Double-click to run — that's it
3. Data is local (SQLite)

### Scenario B — Shared team tool with central database
1. Set up MySQL on a server (or use existing SQL server)
2. Edit `config/settings.py` with MySQL credentials
3. Rebuild the EXE: `pyinstaller build.spec`
4. Distribute `CarbonEmissionCalculator.exe` to all users
5. All users share the same MySQL database

### Scenario C — Network share / Streamlit server
1. Run `streamlit run app.py --server.port 8501` on a server
2. Users access via browser: `http://<server-ip>:8501`
3. No EXE needed; works on any OS

---

## 🧮 Excel Formula Mapping

| Excel Cell | Python Function | Description |
|------------|----------------|-------------|
| E16/G16/H16 | `corrugated_adjusted_dims()` | Dims + 40mm clearance |
| M16 | `corrugated_box_area()` | Ply-adjusted surface area (m²) |
| N16 | `corrugated_box_weight()` | Ply weight-adjusted (kg) |
| E19/G19/H19 | `wooden_box_adjusted_dims()` | Dims + 40mm clearance |
| M19 | `wooden_box_volume()` | Hollow box net volume (m³) |
| N19 | `wooden_box_weight()` | Weight @ 600 kg/m³ |
| M22 | `pallet_volume()` | Deck+Runner+Plank total (m³) |
| N22 | `pallet_weight()` | Weight @ 500 kg/m³ |
| E30 | `material_co2_corrugated()` | wt × 0.491 kgCO₂/kg |
| H30 | `material_co2_wooden_box()` | wt × wood factor |
| K30 | `material_co2_pallet()` | wt × pallet wood factor |
| Backup!H32 | `transport_co2_design()` | dist × (kg/1000) × factor |
| Backup!H38 | `transport_co2_physical()` | Physical input transport |

### Emission Factors (from Backup calculations sheet)
| Source | Factor |
|--------|--------|
| Corrugation (Backup!C15) | 0.491 kgCO₂/kg |
| Solidwood (Backup!C18) | 0.31 kgCO₂/kg |
| Plywood (Backup!C19) | 0.68 kgCO₂/kg |
| Road (Backup!H15) | 0.062 kgCO₂/tonne·km |
| Rail (Backup!H16) | 0.022 kgCO₂/tonne·km |
| Sea (Backup!H17) | 0.016 kgCO₂/tonne·km |
| Air (Backup!H18) | 0.61 kgCO₂/tonne·km |

---

## ✅ Validation Test (L=600, W=400, H=300, 5-ply, t=20mm)

```
Corrugated area:   2.724960 m²   ← matches Excel M16
Corrugated weight: 2.861208 kg   ← matches Excel N16
Wooden box vol:    0.012416 m³   ← matches Excel M19
Wooden box wt:     7.449600 kg   ← matches Excel N19
Pallet volume:     0.023651 m³   ← matches Excel M22
Pallet weight:    11.825550 kg   ← matches Excel N22
Transport (Air, 1000km): 15.0589 kg CO₂  ← matches Backup!H32
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No module named streamlit" | `pip install streamlit` |
| MySQL connection refused | Check host/port in settings.py, ensure MySQL is running |
| EXE doesn't open | Right-click → Run as Administrator |
| Browser doesn't open | Manually go to http://localhost:8501 |
| Port already in use | App auto-finds next free port (8501–8600) |
