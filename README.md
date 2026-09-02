# Airline Delay Intelligence (Python / Streamlit)

DSS 2026 group project. Stack: **pandas** (clean) · **Plotly** (charts) · **Streamlit** (dashboard).

## Frozen dataset

- **File:** `Flight_Delays_Cleaned.csv` (~10 MB, 50,000 rows, 2015)
- **Kaggle:** https://www.kaggle.com/datasets/saurabhanand56/us-flight-delays-2015-cleaned-50k-ml-ready
- **Put the CSV in** `raw/` (do not commit the CSV if the repo is shared publicly)

Cancel rate on the Kaggle preview was ~2%, so this is an operations sample, not a balanced ML extract.

## Setup (Windows)

```text
cd "Decision support Systems/DSS project/DSS-Airline-Delay"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Download `Flight_Delays_Cleaned.csv` from the Kaggle page above into `raw/`.

```text
streamlit run dashboard/app.py
```

Dashboard **layout** rules (filters, cards, chart units, missing parquet): `dashboard/DASHBOARD.md`.  
KPI **formulas**: `KPI_DICTIONARY.md`.

## Layout

```text
raw/          Person A: original CSV
sample/       optional smaller slice while building
clean/        Person A publishes tables the dashboard loads
src/          pandas clean pipeline
dashboard/    Streamlit app (Person B)
```
