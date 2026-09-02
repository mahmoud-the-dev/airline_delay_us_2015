# Dashboard layout contract

**Formulas live in** `KPI_DICTIONARY.md` **and** `metrics.py`.  
**This file is how the Streamlit page is allowed to behave.** Copy these rules on every later tab. Do not keep the contract only as comments in `app.py`.

PoC today = one page (slim BQ1). Final app = four tabs, same contract.

---

## Load

- Load **only** `clean/flights.parquet` (BQ5 later may also load `clean/delay_risk_bands.parquet`).
- Wrap the load in `@st.cache_data`.
- If parquet is missing: `st.error` telling the user to run `python src/clean.py`, then `st.stop()`.
- **Never** read `raw/Flight_Delays_Cleaned.csv` in the app.
- Keep title + source caption. Do not keep the old success/warning/info stub once the dashboard is live.

---

## Filter

- One sidebar filter frame shared by the whole page (and later by all tabs).
- Airline: `filtered = df[df["AIRLINE_NAME"].isin(selected)]`.
- **Empty multiselect = no rows**, not “all airlines.” KPIs go to 0 flights / `nan` rates. **Reset** is the only path back to all airlines.
- Sidebar help: clearing the list shows no flights; Reset restores all.
- Month (and other cuts) later: same honesty — empty means empty, not “ignore this filter.”

---

## KPI cards

- Three columns of `st.metric` (PoC). Later tabs may add cancel rate, etc., still via `metrics.py` only.
- Call `metrics.flights`, `metrics.delay_rate`, `metrics.avg_delay_minutes` on **`filtered`**. No `mean()` / `/` in the layout.
- **Flights:** integer with thousands separators. `0` is a real count.
- **Delay rate:** 0–1 float shown as percent, one decimal (`18.2%`).
- **Avg delay:** one decimal + ` min`.
- If `delay_rate` or `avg_delay_minutes` is `nan` (`pd.isna`): show **—**, never `0%` or `0 min`.

---

## Delay-rate charts

- Population = **operated** rows of `filtered` (`metrics.operated` or the same mask).
- Series = `["DELAYED"].mean()` as **0–1**. Do not multiply by 100 in pandas.
- Plotly axis **and** hover: percent ticks (e.g. `.1%`) so they match the card.
- Chart A (airlines): groupby `AIRLINE_NAME`, sort worst delay rate first.
- Chart B (month): groupby `MONTH` (1–12). Axis title `Month`. `xaxis` type `category` with `categoryarray=[1..12]` so January stays left. Missing months = gap, not interpolated.
- Cancelled/diverted belong on cancel-rate views later, not in these delay-rate charts.

---

## Final four tabs (do not build in the PoC)

Same load, sidebar, cards, operated groupby, percent ticks, `nan` → —.

| Tab | Content | BQs |
|-----|---------|-----|
| 1 Overview | KPIs; delay rate by airline; by month; later top-15 origins | BQ1 |
| 2 Causes | Cause-minute shares | BQ2 |
| 3 Time & risk | DOW, time-block, heatmap; historical risk bands | BQ3, BQ5 |
| 4 Cancels vs delay | Cancel rate; delay vs cancel scatter | BQ4 (+ leftover BQ1) |

No fifth tab for BQ5.

---

## What this file is not

- Not KPI definitions (see `KPI_DICTIONARY.md`).
- Not cleaning rules (see `DATA_DICTIONARY.md` + `src/clean.py`).
- Not the rubric / business-question freeze (see `AIRLINE_DELAY_GROUP_PROTOCOL_PYTHON.md` one folder up).
