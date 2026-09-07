# Dashboard layout contract

**Formulas live in** `KPI_DICTIONARY.md` **and** `metrics.py`.  
**This file is how the Streamlit page is allowed to behave.** Copy these rules on every later tab. Do not keep the contract only as comments in `app.py`.

Four tabs in `dashboard/app.py`, same contract on every tab.

---

## Load

- Load **only** `clean/flights.parquet`. BQ5 also loads `clean/delay_risk_bands.parquet` (`@st.cache_data`). If the bands file is missing, the Time & risk tab warns and skips the lookup; the rest of the app still runs.
- If `flights.parquet` is missing: `st.error` telling the user to run `python src/clean.py`, then `st.stop()`. For Streamlit Cloud, keep `clean/flights.parquet` in git so that file exists on deploy.
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
- Chart F (weekday, Time & risk): groupby `DOW_NAME`, Monday → Sunday.
- Chart G (time block, Time & risk): groupby `TIME_BLOCK`, Overnight → Morning → Afternoon → Evening → Night.
- Chart H (heatmap, Time & risk): weekday × time-block, operated `DELAYED` mean, percent colorbar. Empty cells = gap.
- Chart D (top 15 origins, Overview): `metrics.top_origins(filtered, n=15)` — busiest IATA origins by flight count; plot `delay_rate` (0–1, percent ticks). Unmatched BTS IDs are dropped from this chart only. Do not drop all of October.
- Chart E (avg delay minutes by airline, Overview): `metrics.delayed_operated(filtered)`, groupby `AIRLINE_NAME` mean `ARRIVAL_DELAY`, worst first. Same grain as the avg-delay card.
- Cancelled/diverted belong on cancel-rate views (Cancels tab), not in these delay-rate charts.
- Airport rankings (top origins/destinations): use `metrics.top_origins` / `metrics.iata_airports` so unmatched BTS IDs are dropped from that chart only. Do not drop all of October.

---

## Cause-minute charts (Causes tab)

- Population = delayed operated rows (`metrics.cause_minutes` / `metrics.cause_share`). Not delay rate.
- Share = each cause’s minutes / sum of the five cause columns. Axis and hover as percent. Do not multiply by 100 in pandas.
- Stacked bar: call `cause_share` / `cause_minutes` per airline. 100% stack (`range` 0–1). Skip airlines with no cause minutes.
- Overall pie (or treemap): `cause_minutes(filtered)` as slice size; percents match `cause_share(filtered)`.
- Caption: causes exist only for arrival delay ≥ 15 min.

---

## Historical risk lookup (Time & risk, BQ5)

- Load `clean/delay_risk_bands.parquet`. Do not rebuild bands in the app.
- Filter by selected airlines (`AIRLINE_NAME`). Empty airline list = no cells. Month does not apply (year-round n≥30 cells).
- Heatmap: weekday × time-block delay rate from the lookup (n-weighted if several airlines). Table: airline, weekday, block, flights, delay rate, `DELAY_RISK_BAND`.
- Caption: historical 2015 risk, not a prediction. Low < 15%, Medium 15% to < 25%, High ≥ 25%.

---

## Cancel vs delay (Cancels tab)

- Cancel rate = `metrics.cancel_rate` on all rows in the filter (cancelled ÷ flights), not operated-only. Axis and hover as percent.
- Chart I: cancel rate by airline, worst first. Call `cancel_rate` per airline.
- Chart J: scatter delay rate vs cancel rate; size = `flights`. Both axes 0–1 with percent ticks. Delay rate still uses `metrics.delay_rate` (operated).
- Optional cancel-reason mix: among cancelled rows only (`CANCEL_REASON_NAME`), 100% stack by airline plus overall pie. Not a delay-rate chart.

---

## Four tabs

Same load, sidebar, cards, operated groupby, percent ticks, `nan` → —.

| Tab | Content now | Later | BQs |
|-----|-------------|-------|-----|
| 1 Overview | KPIs; delay rate by airline; vs overall; by month; top-15 origins; avg delay minutes by airline | — | BQ1 |
| 2 Causes | KPIs; cause-minute share stacked by airline; overall pie | — | BQ2 |
| 3 Time & risk | KPIs; delay rate by weekday, time block, weekday×block heatmap, hour; historical risk heatmap + table | — | BQ3, BQ5 |
| 4 Cancels vs delay | KPIs; cancel rate by airline; delay vs cancel scatter (size = flights); cancel-reason mix | — | BQ4 |

No fifth tab for BQ5.

---

## What this file is not

- Not KPI definitions (see `KPI_DICTIONARY.md`).
- Not cleaning rules (see `DATA_DICTIONARY.md` + `src/clean.py`).
- Not the rubric / business-question freeze (see `AIRLINE_DELAY_GROUP_PROTOCOL_PYTHON.md` one folder up).
