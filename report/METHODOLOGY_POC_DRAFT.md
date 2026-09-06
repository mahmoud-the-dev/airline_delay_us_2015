# Methodology

This draft will be expanded, not replaced, for the 7 September PDF. Sections a, b, and c stay.

### a. Data cleaning and preparation

The working file is `raw/Flight_Delays_Cleaned.csv`, 50,000 rows from the 2015 BTS on-time extract in the Kaggle 50k pack. `src/clean.py` writes `clean/flights.parquet`, the dashboard never opens the CSV, and the grain stays one row per scheduled flight.

Arrival delay is blank on every cancelled flight and every diverted flight, 794 and 121 rows, because those flights never completed a scheduled arrival. Clock fields that never happened are blank in the same rows, and we did not impute them, because filling arrival delay would invent a landing time. `OPERATED` is false for cancelled and diverted rows, so `DELAYED` cannot treat a blank `ARRIVAL_DELAY` as late. On operated rows `ARRIVAL_DELAY` has no missing values, the Kaggle pack already filled cause-minute columns with zeros, and we left the remaining columns unchanged.

We called `drop_duplicates` and the row count stayed 50,000, because the extract had no duplicate scheduled-flight rows to remove.

`clean.py` does not recast columns, and pandas infers types from the CSV, so `CANCELLED` and `DIVERTED` come in as booleans, delay minutes as floats, and calendar fields as integers, which parquet then stores. For the final report we still need to map October 2015 origin and destination from 5-digit BTS IDs to IATA before any airport ranking, and that mapping is not in the current script.

We added `OPERATED` as not cancelled and not diverted, `DELAYED` as operated and `ARRIVAL_DELAY` at least 15 minutes, and `AIRLINE_NAME` from the two-letter code, keeping the raw code if a name were missing, which never happened in this extract. Time-of-day blocks are planned for final and are not in the parquet yet.

No normalization was applied to any column. The stored table stays flight-level, while the app groups operated rows by airline and by month.

### b. Modeling / dashboard design

We structured the table for a filterable BI page. pandas writes the clean table, `dashboard/metrics.py` holds the KPI functions, and Streamlit plus Plotly draw the page, while we froze the definitions in `KPI_DICTIONARY.md` and the page calls `flights`, `delay_rate`, and `avg_delay_minutes` on the filtered frame instead of recomputing those ratios in the layout.

The sidebar has a single filter on airline names. Clearing the list leaves zero rows, so the flights card shows 0 and delay rate and average delay show a dash rather than 0% or 0 min, and Reset is the only control that puts every airline back. Month filters are planned for final.

The page is a single screen with three cards and two delay-rate charts. The Flights card counts filtered rows including cancelled and diverted, the delay-rate card is delayed operated flights divided by operated flights shown to one decimal percent, and avg delay minutes is the mean `ARRIVAL_DELAY` among delayed operated flights only. Both charts use the same operated `DELAYED` mean, so the axis stays 0 to 1 with percent ticks and matches the delay-rate card. Horizontal bars rank airlines with the worst delay rate first, and a line by `MONTH` 1 through 12 keeps January on the left and leaves a gap if a month is empty rather than drawing a slope through missing points. Cancelled and diverted rows stay out of those two charts, and causes, time and risk, and cancel-versus-delay tabs are planned for final.

### c. Optional AI/BI modeling

We have not implemented optional AI or BI modeling yet. For the final PDF we will add a historical delay-risk band table with Low / Medium / High bands from delay rate at airline by day-of-week by time-block, dropping cells with fewer than 30 flights. The method is a BI lookup, not sklearn and not a 2016 forecast.
