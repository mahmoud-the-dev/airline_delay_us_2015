"""Load parquet and print delay_rate from dashboard/metrics (~0.18). Same number must appear in the app later."""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dashboard.metrics import delay_rate, avg_delay_minutes

df = pd.read_parquet(ROOT / "clean" / "flights.parquet")
rate = delay_rate(df)
print("delay_rate:", rate, "  (≈ 0.18; same number must appear in the app)")
print("avg_delay_minutes:", avg_delay_minutes(df), "  (≈ 10.5; same number must appear in the app)")