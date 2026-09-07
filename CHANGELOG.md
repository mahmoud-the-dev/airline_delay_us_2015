# Changelog (Person A)

- 2026-09-07: Cancels vs delay BQ4: cancel rate by airline, delay vs cancel scatter (size = flights), cancel-reason mix.
- 2026-09-07: Time & risk BQ3 (weekday, time block, heatmap, hour) and BQ5 (`delay_risk_bands.parquet` heatmap + table; historical 2015, not a prediction).
- 2026-09-07: Causes BQ2: cause-minute share stacked by airline plus overall pie (`cause_share` / `cause_minutes`).
- 2026-09-07: Overview BQ1: top-15 origin delay rates via `top_origins`, avg delay minutes by airline, delay rate minus overall.
- 2026-09-07: Four-tab dashboard shell (`st.tabs`), shared airline+month sidebar, parquet-only load, KPI row (incl. cancel rate) on every tab; hour chart moved to Time & risk.
- 2026-09-07: KPI functions complete.
- 2026-09-07: Map October 5-digit BTS origin/dest IDs to IATA in `src/clean.py`; leftover IDs stay numeric and are flagged off airport charts only.
- 2026-09-03: Track `clean/flights.parquet` so Streamlit Cloud can load the dashboard without a local `src/clean.py` run.
- 2026-09-03: PoC dashboard page locked in `dashboard/DASHBOARD.md` (parquet-only load, empty filter = no rows, metrics-only KPI cards, operated delay-rate charts, percent ticks, nan → —).
- 2026-09-02: KPI dictionary v1 frozen (arrival ≥ 15, operated flights, avg delay among delayed). Same rules for PoC and submission.
- 2026-08-29: Downloaded Kaggle zip into `raw/`, extracted `Flight_Delays_Cleaned.csv` (50,000 × 37, cancel rate 1.59%).
- 2026-08-28: Frozen Kaggle 2015 50k extract; project folder and Python env created.
