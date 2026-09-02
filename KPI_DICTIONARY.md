# KPI dictionary v1 — frozen 2 Sep 2026

PoC and final project use the **same** rules. Any number on the dashboard or in the PDF must come from `dashboard/metrics.py`.

## Freeze (do not reopen)

1. **Delayed** = `ARRIVAL_DELAY >= 15`
2. **Operated** = not cancelled and not diverted
3. **Delay rate** = delayed operated flights / operated flights
4. **Avg delay minutes** = mean `ARRIVAL_DELAY` among **delayed** operated flights

## KPI formulas

| KPI                 | Definition                                                                                                                  | Notes                                                         |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Flights             | Count of rows in the current filter                                                                                         | Includes cancelled/diverted                                   |
| Operated flights    | Rows that are not cancelled and not diverted                                                                                | Denominator for delay rate                                    |
| Delayed flight      | Operated **and** `ARRIVAL_DELAY >= 15`                                                                                      | DOT-style threshold                                           |
| Delay rate          | Delayed / operated                                                                                                          | Not delayed / all rows                                        |
| Avg delay minutes   | Mean arrival delay among delayed operated flights                                                                           | Not the mean of all flights                                   |
| Total delay minutes | Sum of `ARRIVAL_DELAY` among delayed operated flights                                                                       |                                                               |
| Cause share         | Each cause’s minutes / sum of the five cause columns                                                                        | Only filled when arrival delay ≥ 15 (BQ2; not needed for PoC) |
| Cancel rate         | Cancelled / flights (all rows in filter)                                                                                    | BQ4; not needed for PoC                                       |
| Divert rate         | Diverted / flights                                                                                                          | Side KPI only                                                 |
| Delay risk band     | Low / Medium / High from historical delay rate at airline × day-of-week × time-block; drop cells with fewer than 30 flights | BQ5; not needed for PoC                                       |

**Cause columns:** `AIRLINE_DELAY` (Carrier), `WEATHER_DELAY`, `AIR_SYSTEM_DELAY` (NAS), `SECURITY_DELAY`, `LATE_AIRCRAFT_DELAY`.
