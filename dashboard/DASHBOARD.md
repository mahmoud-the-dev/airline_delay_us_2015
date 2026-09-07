# Dashboard layout contract

**Formulas live in** `KPI_DICTIONARY.md` **and** `metrics.py`.  
**This file is how the Streamlit page is allowed to behave.** Copy these rules on every later tab. Do not keep the contract only as comments in `app.py`.

Four tabs in `dashboard/app.py`, same contract on every tab.

---

## Load

- Load **only** `clean/flights.parquet` (BQ5 later may also load `clean/delay_risk_bands.parquet`).
- Wrap the load in `@st.cache_data`.
- If parquet is missing: `st.error` telling the user to run `python src/clean.py`, then `st.stop()`. For Streamlit Cloud, keep `clean/flights.parquet` in git so that file exists on deploy.
- **Never** read `raw/Flight_Delays_Cleaned.csv` in the app.
- Keep title + source caption. Do not keep the old success/warning/info stub once the dashboard is live.

---

## Filter

- One sidebar filter frame shared by all tabs. Filter **once**; every tab uses that same `filtered` frame.
- Airline: `df["AIRLINE_NAME"].isin(selected_airlines)`.
- Month: `df["MONTH"].isin(selected_months)` with options 1–12.
- **Empty multiselect = no rows**, not “ignore this filter.” KPIs go to 0 flights / `nan` rates.
- **Reset** is the only path that puts both lists back to all.
- Sidebar help: clearing a list shows no flights; Reset restores all airlines and months.

---

## KPI cards

- Four columns of `st.metric` on **every** tab: Flights, Delay rate, Avg delay minutes, Cancel rate.
- Call `metrics.flights`, `metrics.delay_rate`, `metrics.avg_delay_minutes`, `metrics.cancel_rate` on **`filtered`**. No `mean()` / `/` in the layout.
- **Flights:** integer with thousands separators. `0` is a real count.
- **Delay rate:** 0–1 float shown as percent, one decimal (`18.2%`).
- **Avg delay:** one decimal + ` min`.
- If `delay_rate`, `avg_delay_minutes`, or `cancel_rate` is `nan` (`pd.isna`): show **—**, never `0%` or `0 min`.

---

## Delay-rate charts

- Population = **operated** rows of `filtered` (`metrics.operated` or the same mask).
- Series = `["DELAYED"].mean()` as **0–1**. Do not multiply by 100 in pandas.
- Plotly axis **and** hover: percent ticks (e.g. `.1%`) so they match the card.
- Chart A (airlines): groupby `AIRLINE_NAME`, sort worst delay rate first.
- Chart A2 (vs overall, Overview): same airline delay rates minus `metrics.delay_rate(filtered)`. Positive = worse than the KPI card. Zero line at 0. Skip when overall rate is `nan`.
- Chart B (month): groupby `MONTH` (1–12). Axis title `Month`. `xaxis` type `category` with `categoryarray=[1..12]` so January stays left. Missing months = gap, not interpolated.
- Chart C (hour, Time & risk): groupby `DEP_HOUR` (0–23). Clock order, not worst-first. Same `category` + `categoryarray` pattern as month. Missing hours = gap. Overnight bins are small-*n*; do not treat them as a ranking.
- Chart D (top 15 origins, Overview): `metrics.top_origins(filtered, n=15)` — busiest IATA origins by flight count; plot `delay_rate` (0–1, percent ticks). Unmatched BTS IDs are dropped from this chart only. Do not drop all of October.
- Chart E (avg delay minutes by airline, Overview): `metrics.delayed_operated(filtered)`, groupby `AIRLINE_NAME` mean `ARRIVAL_DELAY`, worst first. Same grain as the avg-delay card.
- Cancelled/diverted belong on cancel-rate views later, not in these delay-rate charts.
- Airport rankings (top origins/destinations): use `metrics.top_origins` / `metrics.iata_airports` so unmatched BTS IDs are dropped from that chart only. Do not drop all of October.

---

## Four tabs

Same load, sidebar, cards, operated groupby, percent ticks, `nan` → —.

| Tab | Content now | Later | BQs |
|-----|-------------|-------|-----|
| 1 Overview | KPIs; delay rate by airline; vs overall; by month; top-15 origins; avg delay minutes by airline | — | BQ1 |
| 2 Causes | KPIs only | cause-minute shares | BQ2 |
| 3 Time & risk | KPIs; delay rate by scheduled hour | DOW, time-block, heatmap; historical risk bands | BQ3, BQ5 |
| 4 Cancels vs delay | KPIs only | cancel rate views; delay vs cancel scatter | BQ4 (+ leftover BQ1) |

No fifth tab for BQ5.

---

## What this file is not

- Not KPI definitions (see `KPI_DICTIONARY.md`).
- Not cleaning rules (see `DATA_DICTIONARY.md` + `src/clean.py`).
- Not the rubric / business-question freeze (see `AIRLINE_DELAY_GROUP_PROTOCOL_PYTHON.md` one folder up).
