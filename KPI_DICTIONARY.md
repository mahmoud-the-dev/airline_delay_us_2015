# KPI dictionary v0 (freeze with Person B+C)

Any PDF number must match a function in `dashboard/metrics.py`.

| KPI | Definition (draft) | Owner of formula |
|-----|--------------------|------------------|
| Flights | Count of flight records in scope | B (`metrics.py`) / A (grain) |
| Delayed flight | Arrival (or departure) delay ≥ 15 minutes — **pick arrival vs departure and freeze** | C+B lock |
| Delay rate | Delayed flights / flights | B |
| Avg delay minutes | Average delay among delayed **or** all flights — **pick one and freeze** | C+B |
| Total delay minutes | Sum of delay minutes | B |
| Cause share | Cause minutes / total cause minutes (Airline/Carrier, Weather, Air System/NAS, Security, Late Aircraft) | B |
| Cancel rate | Cancelled / flights | B |
| Divert rate | Diverted / flights — side KPI only (not a locked BQ; too few rows for airport cuts) | B |
| Delay risk band | Low / Medium / High from historical delay rate at airline × day-of-week × time-block; apply a volume floor (e.g. ≥30 flights). Not a forecast. | A (table) / B (`metrics.py`) |

Draft delay threshold = **≥ 15 minutes** (DOT convention). Confirm at Sync-1.
