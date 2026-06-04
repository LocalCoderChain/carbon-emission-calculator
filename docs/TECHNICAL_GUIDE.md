# Carbon Emission Calculator — Complete Technical Guide
## For Team Presentation & Developer Handover
### Atlas Copco | v1.0.0



---

# PART 1 — HOW TO TEST THE CALCULATOR

## Step-by-Step Test with Known Values

Use these exact inputs to verify the app matches the Excel sheet:

| Field | Test Value |
|---|---|
| Length | 600 mm |
| Width | 400 mm |
| Height | 300 mm |
| Box Ply | 5 |
| Box Thickness | 20 mm |
| Wood Type (Box) | Solidwood |
| Wood Type (Pallet) | Plywood |
| Include Corrugated Box | Yes (checked) |
| Include Wooden Box | Yes (checked) |
| Transport Type | Air |
| Product Weight | 10 kg |
| Distance | 1000 km |

### Expected Outputs (verified against Excel):

| Output | Expected Value | Excel Cell |
|---|---|---|
| Corrugated Box Area | 2.724960 m² | M16 |
| Corrugated Box Weight | 2.861208 kg | N16 |
| Wooden Box Volume | 0.012416000 m³ | M19 |
| Wooden Box Weight | 7.449600 kg | N19 |
| Pallet Volume | 0.023651100 m³ | M22 |
| Pallet Weight | 11.825550 kg | N22 |
| Corrugated CO₂ | 1.404853 kg | E30 |
| Pallet CO₂ (Plywood) | 8.041374 kg | K30 |
| Transport CO₂ (Air, 1000km) | 15.058922 kg | Backup!H32 |
| **Total Design CO₂** | **~24.50 kg** | Sum |

If your app shows these values → it is working correctly and matches Excel exactly.

---

# PART 2 — HOW THE CALCULATOR WORKS (Full Explanation)

## Overview

The calculator has **two parallel calculation paths**, both derived from the Excel sheet:

```
Path A — DESIGN CALCULATION
  → You enter product dimensions + material choices
  → The app calculates weights from geometry
  → Used when you don't know actual material weights

Path B — PHYSICAL INPUT
  → You directly enter the known weight of each material
  → Used when you have weighed the actual packaging
  → More accurate if weights are available
```

Both paths produce CO₂ emissions. The app shows which is more sustainable.

---

## 2.1 — The 40 mm Clearance Buffer

**Excel cells: E16, G16, H16, E19, G19, H19, E22, G22**

```
Formula: Adjusted_Dimension = Product_Dimension + 40
```

**Why?**
When you manufacture a corrugated box or wooden box, the box must be slightly
larger than the product inside it so:
- The product fits without force
- There is room for cushioning/foam
- The flaps can close properly

The Excel uses a fixed 40 mm clearance on each dimension (length, width, height).
This is a standard packaging engineering assumption.

**Example:**
- Product: 600 × 400 × 300 mm
- Box (after buffer): 640 × 440 × 340 mm
- The box is calculated at these larger dimensions

The pallet also uses the same buffered dimensions (it must accommodate the box).

---

## 2.2 — Corrugated Box: Surface Area & Ply Adjustment

**Excel cells: M16 (area), N16 (weight)**

### Step 1 — Base Surface Area
```
Base SA = 2 × (L×W + L×H + W×H)   [in mm²]
```
This is the standard formula for surface area of a rectangular box.
For 640×440×340 mm:
  Base SA = 2 × (640×440 + 640×340 + 440×340)
          = 2 × (281,600 + 217,600 + 149,600)
          = 2 × 648,800
          = 1,297,600 mm²

### Step 2 — Ply Factor (the corrugation multiplier)
Corrugated board is not a single flat sheet — it has layers of fluted paper
sandwiched between liners. More plies = more material = more surface area needed.

| Ply | Excel Formula | Why this factor? |
|---|---|---|
| 3-ply | SA + SA × 170/100 | Light duty — single wall, 1 flute layer |
| 5-ply | SA + SA × 110/100 | Medium duty — double wall, 2 flute layers |
| 7-ply | SA + SA × 105/100 | Heavy duty — triple wall, 3 flute layers |

**Note:** The factor is ADDED to the base, not replacing it:
```
Adjusted SA = Base SA + (Base SA × factor)
```

For 5-ply:
  Adjusted SA = 1,297,600 + (1,297,600 × 110/100)
              = 1,297,600 + 1,427,360
              = 2,724,960 mm²
  Area in m²  = 2,724,960 / 1,000,000
              = 2.72496 m²   ← matches Excel M16

### Step 3 — Weight from Area (Ply Weight Adjustment)
The weight of corrugated board is proportional to its area, but the density
varies by ply. The Excel uses the area (m²) directly as a weight proxy,
then adjusts by ply:

| Ply | Adjustment | Reasoning |
|---|---|---|
| 3-ply | Area × (1 - 0.25) | Lighter single-wall board, less paper per m² |
| 5-ply | Area × (1 + 0.05) | Standard medium-weight board |
| 7-ply | Area × (1 + 0.45) | Heavy triple-wall, significantly more paper |

For 5-ply:
  Weight = 2.72496 × (1 + 0.05)
         = 2.72496 × 1.05
         = 2.861208 kg   ← matches Excel N16

**Excel source:** Backup calculations sheet — factors derived from FEFCO
(European Federation of Corrugated Board Manufacturers) industry data.

---

## 2.3 — Wooden Box: Hollow Volume Method

**Excel cells: M19 (volume), N19 (weight)**

A wooden box is a hollow shell. You cannot just calculate outer volume —
you must subtract the hollow inside.

```
Outer Volume = L × W × H               (full solid block)
Inner Volume = (L-t) × (W-t) × (H-t)  (the hollow space, where t = wall thickness)
Net Volume   = Outer - Inner           (just the wood material)
Volume (m³)  = Net / 1,000,000,000     (convert mm³ → m³)
Weight (kg)  = Volume × 600            (600 kg/m³ = density of solid wood)
```

**Why 600 kg/m³?**
This is the standard density of common structural timber (pine/spruce).
The Excel Backup sheet uses this figure. Plywood is denser (680 kg/m³)
but the box formula uses solid wood density.

**Example with t=20mm, 640×440×340:**
  Outer = 640 × 440 × 340         = 95,744,000 mm³
  Inner = (640-20)×(440-20)×(340-20)
        = 620 × 420 × 320         = 83,328,000 mm³
  Net   = 95,744,000 - 83,328,000 = 12,416,000 mm³
  Vol   = 12,416,000 / 1e9        = 0.012416 m³  ← Excel M19
  Wt    = 0.012416 × 600          = 7.4496 kg    ← Excel N19

---

## 2.4 — Wooden Pallet: Three-Component Structure

**Excel cells: M22 (volume), N22 (weight)**

A standard wooden pallet has 3 structural components. ALL are fixed dimensions
in the Excel (your product size only affects the deck):

```
Component 1 — DECK (the flat top board)
  Dimensions: Pallet_L × Pallet_W × 36 mm (height)
  Count: 1
  Excel row 23: E23=E22, G23=G22, H23=36, I23=1

Component 2 — RUNNERS/BLOCKS (the legs)
  Dimensions: 125 × 110 × 90 mm (fixed)
  Count: 9
  Excel row 24: E24=125, G24=110, H24=90, I24=9

Component 3 — PLANKS (the bottom boards)
  Dimensions: Pallet_W × 90 × 20 mm
  Count: 3
  Excel row 25: E25=G22, G25=90, H25=20, I25=3
```

```
Total Volume = (Deck_L×Deck_W×36×1 + 125×110×90×9 + Pallet_W×90×20×3) / 1e9
Total Weight = Total Volume × 500    (500 kg/m³ = density of plywood pallet)
```

**Why 500 kg/m³?**
Pallets are typically made of lighter plywood or softwood. 500 kg/m³ is the
Excel's fixed assumption (Backup sheet, pallet density).

**Why 9 runners?**
A standard EUR/EPAL pallet has a 3×3 grid of blocks — 9 total.

---

## 2.5 — Material CO₂ Emissions

**Excel cells: E30 (corrugated), H30 (wooden box), K30 (pallet)**

Each material has a published CO₂ emission factor — how much CO₂ was
released to manufacture 1 kg of that material:

```
CO₂ = Weight_kg × Emission_Factor
```

| Material | Factor (kgCO₂/kg) | Source (Excel sheet) | Excel Cell |
|---|---|---|---|
| Corrugated paper | 0.491 | FEFCO industry average | Backup!C15 |
| Solid wood | 0.310 | Climatiq database | Backup!C18 |
| Plywood | 0.680 | OpenCO2.net / Climatiq | Backup!C19 |
| LDPE plastic | 2.792 | Climatiq | Backup!E15 |
| HDPE plastic | 2.506 | Climatiq | Backup!E16 |
| PP plastic | 3.576 | Climatiq | Backup!E17 |
| LLDPE plastic | 2.587 | Climatiq | Backup!E18 |
| PS plastic | 2.982 | Climatiq | Backup!E19 |

**Why are plastic factors so much higher than wood?**
Plastics are petrochemical products — derived from fossil fuels. Their
production emits significantly more CO₂ than harvesting and processing wood.

---

## 2.6 — Transport CO₂ Emissions

**Excel cells: Backup!H32 (design), Backup!H38 (physical)**

```
CO₂ = Distance_km × (Total_Weight_kg / 1000) × Emission_Factor

Where:
  Total_Weight = Packaging_Weight + Product_Weight
  Weight is converted to tonnes (÷ 1000)
  Emission_Factor is per tonne-km
```

| Transport Mode | Factor (kgCO₂/tonne·km) | Excel Cell | Source |
|---|---|---|---|
| Road | 0.062 (= 62/1000) | Backup!H15 | McKinnon Report |
| Rail | 0.022 (= 22/1000) | Backup!H16 | McKinnon Report |
| Sea (Ocean) | 0.016 (= 16/1000) | Backup!H17 | McKinnon Report |
| Air | 0.610 | Backup!H18 | ScienceDirect |

**Why is Air so much worse?**
Air freight emits ~10× more CO₂ per tonne-km than sea freight. This is
why the choice of transport mode is often the dominant CO₂ factor.

**Example (Air, 1000km, total weight = 2.86 + 11.83 + 10 = 24.69 kg):**
  CO₂ = 1000 × (24.69 / 1000) × 0.61
       = 1000 × 0.02469 × 0.61
       = 15.06 kg CO₂   ← matches Excel Backup!H32

---

## 2.7 — Physical Input Path

When you know the actual weight of packaging materials (e.g., you weighed them),
enter them directly. The app then:
1. Uses your entered weights instead of calculated ones
2. Combines them per the packaging combination you choose:
   - "Corrugated + Pallet" → CO₂ uses (corrugated_kg + pallet_kg) for transport
   - "Wooden Box + Pallet" → CO₂ uses (wooden_kg + pallet_kg) for transport
3. Applies the same emission factors for materials
4. Applies the same transport formula

**Excel cells: U18, U19, U34**
```
U18 = IF(corrugated selected, U12 + U14, 0)   [corrugated weight + pallet weight]
U19 = IF(wooden selected, U13 + U14, 0)       [wooden weight + pallet weight]
U34 = packaging_weight + product_weight        [total shipment weight]
```

---

# PART 3 — DATABASE: HOW IT WORKS ON YOUR SYSTEM

## The Short Answer

**You do NOT need to install anything for the database to work.**

The app automatically creates and uses a **SQLite** database file. SQLite is a
file-based database — it's a single `.db` file, built into Python, requiring
zero installation.

## Where is the Database File?

When you run the app, it creates the file here automatically:

| OS | Path |
|---|---|
| Windows | `C:\Users\YourName\carbon_calculator.db` |
| Mac | `/Users/YourName/carbon_calculator.db` |
| Linux | `/home/yourusername/carbon_calculator.db` |

The file is created on first run. If you delete it, it's recreated (empty) next run.

## What's Inside the Database?

One table: `calculations`

```sql
CREATE TABLE calculations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    input_json  TEXT,      -- all input fields stored as JSON
    output_json TEXT,      -- all calculated results stored as JSON
    description TEXT,      -- the note/description you type
    timestamp   TEXT       -- date and time of calculation
);
```

Every time you click CALCULATE, one row is added.

## Can I Open the .db File?

Yes. Use **DB Browser for SQLite** (free, download from sqlitebrowser.org).
Open the `.db` file and you can see all records as a table, export to CSV, etc.

---

## MySQL Option (for Team/Company Use)

If the company wants a **central shared database** (all users save to one place):

1. IT installs MySQL Server on a company server
2. You edit `config/settings.py`:
   ```python
   DB_CONFIG = {
       "use_mysql": True,           # ← change this
       "host":     "192.168.1.50",  # ← server IP
       "port":     3306,
       "user":     "carbon_user",
       "password": "yourpassword",
       "database": "carbon_calculator",
   }
   ```
3. Rebuild the EXE: `pyinstaller build.spec`
4. Share the new EXE — all users connect to the same MySQL database

The app creates the database and table automatically — IT does not need to
run any SQL scripts manually.

---

## EXE + Database: Where Does Everything Live?

### With SQLite (default):
```
CarbonEmissionCalculator.exe    ← can be ANYWHERE (Desktop, USB drive, etc.)
C:\Users\YourName\carbon_calculator.db   ← ALWAYS here, auto-created
```

The EXE and database do NOT need to be in the same folder.
The EXE finds the DB via the user's home directory path.

### With MySQL:
```
CarbonEmissionCalculator.exe    ← on each user's PC (anywhere)
MySQL Server                    ← on a company server (separate machine)
```

The EXE connects to MySQL over the network. No local DB file is used.

### Important Note About the EXE:
The EXE contains ALL of the Python code (app.py, formulas.py, db.py, etc.)
bundled inside it. When the user double-clicks it:
1. It extracts the Python code to a temp folder
2. Starts a local web server (Streamlit) on port 8501
3. Opens the browser automatically
4. When the browser window is closed, the server keeps running in the background

To stop the app: close the browser AND the EXE process in Task Manager.

---

# PART 4 — PYINSTALLER: STEP-BY-STEP

## Prerequisites (do this once on your build machine)

```bash
# 1. Make sure you have Python 3.10+ installed
python --version

# 2. Install all dependencies
pip install -r requirements.txt

# 3. Install PyInstaller
pip install pyinstaller

# 4. Verify streamlit is installed
streamlit --version
```

## Creating a Custom Icon

1. Create or download a `.ico` file (Windows icon format)
   - Free tool: https://convertio.co/png-ico/
   - Recommended size: 256×256 px
2. Save it as `assets/icon.ico` inside your project folder
3. In `build.spec`, uncomment this line:
   ```python
   # icon="assets/icon.ico",   ← remove the # at the start
   ```

## Building the EXE

```bash
# Navigate to your project folder
cd carbon_calculator

# Run PyInstaller using the spec file
pyinstaller build.spec

# Wait 2-5 minutes for bundling...
# Output will be in: dist/CarbonEmissionCalculator.exe
```

## Testing the EXE Before Distributing

```bash
# Run directly from dist folder
dist\CarbonEmissionCalculator.exe
```

- Browser should open at http://localhost:8501
- Test a calculation and verify it saves
- Check `C:\Users\YourName\carbon_calculator.db` was created

## What to Share with the Company

**Option A — Single User:**
Share only: `CarbonEmissionCalculator.exe`
That's it. One file. No installation needed.

**Option B — Team with Central DB:**
1. Set up MySQL first (IT team)
2. Set credentials in `config/settings.py`
3. Rebuild EXE
4. Share: `CarbonEmissionCalculator.exe`
   The EXE will connect to the MySQL server automatically.

---

# PART 5 — EXCEL vs PYTHON: EXACT CELL MAPPING TABLE

| Excel Sheet | Cell | Formula | Python File | Function/Variable |
|---|---|---|---|---|
| Calculator | E16 | `=IF($M$12=TRUE,$E$12+40,0)` | formulas.py | `corrugated_adjusted_dims()` |
| Calculator | G16 | `=IF($M$12=TRUE,$G$12+40,0)` | formulas.py | `corrugated_adjusted_dims()` |
| Calculator | H16 | `=IF($M$12=TRUE,$H$12+40,0)` | formulas.py | `corrugated_adjusted_dims()` |
| Calculator | M16 | `=(2*(E16*G16+E16*H16+G16*H16)+2*(...)*factor)/1000000` | formulas.py | `corrugated_box_area()` |
| Calculator | N16 | `=IF(B16=3,M16-M16*25/100,IF(B16=5,M16+M16*5/100,...))` | formulas.py | `corrugated_box_weight()` |
| Calculator | E19 | `=IF($M$13=TRUE,$E$12+40,0)` | formulas.py | `wooden_box_adjusted_dims()` |
| Calculator | M19 | `=((E19*G19*H19)-((E19-B19)*(G19-B19)*(H19-B19)))/1e9` | formulas.py | `wooden_box_volume()` |
| Calculator | N19 | `=M19*600` | formulas.py | `wooden_box_weight()` |
| Calculator | E22 | `=E12+40` | formulas.py | `pallet_volume()` — pallet_L |
| Calculator | G22 | `=G12+40` | formulas.py | `pallet_volume()` — pallet_W |
| Calculator | H23 | `36` (fixed) | formulas.py | `PALLET_DECK_H = 36` |
| Calculator | E24,G24,H24 | `125, 110, 90` (fixed) | formulas.py | `PALLET_RUNNER_L/W/H` |
| Calculator | I24 | `9` (fixed) | formulas.py | `PALLET_RUNNER_COUNT = 9` |
| Calculator | I25 | `3` (fixed) | formulas.py | `PALLET_PLANK_COUNT = 3` |
| Calculator | M22 | `=((E23*G23*H23)+(E24*G24*H24)*I24+(E25*G25*H25)*I25)/1e9` | formulas.py | `pallet_volume()` |
| Calculator | N22 | `=M22*500` | formulas.py | `pallet_weight()` |
| Calculator | E30 | `=N16*'Backup calculations'!C15` | formulas.py | `material_co2_corrugated()` |
| Calculator | H30 | `=IF(I19=B18, N19*C18, IF(I19=B19, N19*C19))` | formulas.py | `material_co2_wooden_box()` |
| Calculator | K30 | `=IF(K22=B18, N22*C18, IF(K22=B19, N22*C19))` | formulas.py | `material_co2_pallet()` |
| Calculator | X30 | `=IF(T25=D15, E15*W25, IF(...PP..., IF(...)))` | formulas.py | `material_co2_plastic()` |
| Backup | C15 | `0.491` | formulas.py | `EMISSION_FACTORS["Corrugation"]` |
| Backup | C18 | `0.31` | formulas.py | `EMISSION_FACTORS["Solidwood"]` |
| Backup | C19 | `0.68` | formulas.py | `EMISSION_FACTORS["Plywood"]` |
| Backup | E15–E19 | `2.792, 2.506, 3.576, 2.587, 2.982` | formulas.py | `PLASTIC_EMISSION_FACTORS` dict |
| Backup | H15 | `=62/1000` | formulas.py | `TRANSPORT_FACTORS["Road"]` |
| Backup | H16 | `=22/1000` | formulas.py | `TRANSPORT_FACTORS["Rail"]` |
| Backup | H17 | `=16/1000` | formulas.py | `TRANSPORT_FACTORS["Sea (Ocean)"]` |
| Backup | H18 | `0.61` | formulas.py | `TRANSPORT_FACTORS["Air"]` |
| Backup | H32 | `=IF(G32=G15, H30*I30*H15, IF(...))` | formulas.py | `transport_co2_design()` |
| Backup | H38 | `=IF(G38=G15, H36*I36*H15, IF(...))` | formulas.py | `transport_co2_physical()` |
| Backup | I30 | `=Calculator!H34/1000` | formulas.py | `weight_tonnes = total_weight_kg/1000` |

---

# PART 6 — QUICK FAQ FOR YOUR TEAM

**Q: Does the app need internet to run?**
A: No. It runs 100% offline. The fonts load from Google Fonts if internet is
   available, but the calculation engine works without any internet connection.

**Q: If two people run the EXE at the same time on the same machine, do they
   share data?**
A: Yes — they share the same SQLite file. This is fine for a single PC.
   For multi-user across different PCs, use the MySQL option.

**Q: Can the EXE be run from a USB drive?**
A: Yes. The EXE is self-contained. The only external dependency is that the
   database file saves to the user's home directory on whatever PC it runs on.

**Q: What if the port 8501 is already in use?**
A: The launcher automatically tries ports 8501–8600 until it finds a free one.

**Q: Can we export the data to Excel?**
A: The My Calculations page shows all records in a table. Streamlit tables
   have a built-in download button (top-right of the table) to export as CSV,
   which can be opened in Excel.

**Q: How do we back up the data?**
A: Simply copy `carbon_calculator.db` from the user's home folder to a safe
   location. To restore, put it back in the same location.

**Q: The browser opens but shows an error. What do I do?**
A: Wait 5-10 seconds and refresh the page. The app server sometimes takes a
   moment to start before the browser opens.
