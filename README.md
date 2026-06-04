# Carbon Emission Calculator

A Streamlit-based application for estimating carbon emissions generated from packaging materials and transportation methods.

The tool allows users to calculate packaging weight, estimate CO₂ emissions, compare transport modes, and store historical calculations for future analysis.

---

## Features

* Packaging weight estimation based on product dimensions
* Carbon emission calculations for packaging materials
* Transport emission calculations for Road, Rail, Sea, and Air transport
* Historical calculation storage using SQLite
* Search and filter previous calculations
* User-friendly Streamlit interface
* Configurable database support (SQLite / MySQL)

---

## Technology Stack

| Technology | Purpose                  |
| ---------- | ------------------------ |
| Python     | Core application logic   |
| Streamlit  | User Interface           |
| SQLite     | Local data storage       |
| MySQL      | Optional shared database |
| Pandas     | Data handling            |
| NumPy      | Numerical calculations   |

---

## Project Structure

```text
carbon_calculator/
│
├── app.py
├── requirements.txt
├── README.md
│
├── assets/
├── config/
├── database/
├── documentation/
├── screenshots/
└── utility/
```

---

## Installation

### 1. Clone the repository

```bash
git clone <https://github.com/aryabarsode/Carbon_Calculator_App>
cd Carbon_Calculator_App
```

### 2. Install dependencies needed

```bash
pip install -r requirements.txt OR simply run the SETUP.bat file for the same.
```

### 3. Run the application

```bash
streamlit run app.py OR simply click the StartTheApp.bat file.
```

The application will open automatically in your browser.

---

## Database

The application uses SQLite by default and automatically creates the required database on first launch.

MySQL support is also available through the configuration settings, if needed later.

---

## Sample Functionality

The application can calculate:

* Corrugated box weight
* Wooden box weight
* Pallet weight
* Packaging emissions
* Transportation emissions
* Total carbon footprint

Transport modes supported:

* Road
* Rail
* Sea
* Air

---

## Validation

The calculation engine was verified against reference spreadsheet calculations to ensure consistency and accuracy.

Example validation case:

| Output                       | Value        |
| ---------------------------- | ------------ |
| Corrugated Box Area          | 2.724960 m²  |
| Corrugated Box Weight        | 2.861208 kg  |
| Wooden Box Weight            | 7.449600 kg  |
| Pallet Weight                | 11.825550 kg |
| Transport CO₂ (Air, 1000 km) | 15.058922 kg |

---

## Screenshots

Application screenshots are available in the `screenshots/` directory.

---

## Future Improvements

* Export reports to PDF and Excel
* Enhanced analytics dashboard
* Transport mode comparison charts
* Performance optimizations for larger datasets

---

## Author

Developed as an academic and industrial sustainability project focused on packaging and transportation emission analysis.
