# Data dictionary (frozen source)

**Status:** citation frozen 28 Aug 2026 · sample work may start

## Source

| ~Field             | Value                                                                                                                                                           |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Topic              | Airline Delay Intelligence (DSS project 2026, topic 3)                                                                                                          |
| Original collector | USDOT / Bureau of Transportation Statistics (BTS) — 2015 domestic on-time performance                                                                           |
| Kaggle pack        | [US Flight Delays 2015 — Cleaned (50K, ML-Ready)](https://www.kaggle.com/datasets/saurabhanand56/us-flight-delays-2015-cleaned-50k-ml-ready) (`saurabhanand56`) |
| Working file       | `Flight_Delays_Cleaned.csv`                                                                                                                                     |
| License            | Follow the Kaggle page; underlying BTS on-time data is U.S. government public-domain statistical data                                                           |
| Years              | **2015 only**                                                                                                                                                   |
| Rows               | 50,000 (extract of the national 2015 file, not a census)                                                                                                        |
| Grain              | One row = one scheduled flight                                                                                                                                  |
| Sanity check       | Cancelled = **1.59%** in the downloaded file (operations mix, not a 50/50 delay-balanced ML file)                                                               |
| Local path         | `raw/Flight_Delays_Cleaned.csv`                                                                                                                                 |

Cite in the PDF as: _US flight delay data from the Bureau of Transportation Statistics (2015), Kaggle extract “US Flight Delays 2015 — Cleaned (50K)”._

## Scope limits (also Limitations bullets)

- Not 2023/2024 operations; airline map is 2015 (US Airways `US` and Virgin America `VX` still present). Rankings are for 2015, not today’s network.
- 50k rows: rare routes are noisy. Locked BQs use airline / busy origin airports / month / day-of-week / time-block / cancellations — **not** full route rankings or diversion maps.
- **October 2015:** origin/destination are 5-digit BTS IDs, not IATA. Person A must map them before airport views.
- **BQ5 derived table:** `clean/delay_risk_bands.parquet` — historical delay rate by airline × day-of-week × time-block, Low/Med/High bands. Not a forecast.
- Packager already cleaned types and delay-cause zeros; we still engineer delay flags and time blocks. Cause minutes exist only when arrival delay ≥ 15.

## Columns (37, confirmed from local CSV)

**Date:** `YEAR`, `MONTH`, `DAY`, `DAY_OF_WEEK`  
**Identity / route:** `AIRLINE`, `FLIGHT_NUMBER`, `TAIL_NUMBER`, `ORIGIN_AIRPORT`, `DESTINATION_AIRPORT`  
**Times / delays:** `SCHEDULED_DEPARTURE`, `DEPARTURE_TIME`, `DEPARTURE_DELAY`, `TAXI_OUT`, `WHEELS_OFF`, `SCHEDULED_TIME`, `ELAPSED_TIME`, `AIR_TIME`, `DISTANCE`, `WHEELS_ON`, `TAXI_IN`, `SCHEDULED_ARRIVAL`, `ARRIVAL_TIME`, `ARRIVAL_DELAY`  
**Disruption:** `DIVERTED`, `CANCELLED`, `CANCELLATION_REASON`  
**Causes (minutes):** `AIR_SYSTEM_DELAY`, `SECURITY_DELAY`, `AIRLINE_DELAY`, `LATE_AIRCRAFT_DELAY`, `WEATHER_DELAY`  
**Readable times (packager):** `SCHEDULED_DEPARTURE_FMT`, `DEPARTURE_TIME_FMT`, `WHEELS_OFF_FMT`, `WHEELS_ON_FMT`, `SCHEDULED_ARRIVAL_FMT`, `ARRIVAL_TIME_FMT`
