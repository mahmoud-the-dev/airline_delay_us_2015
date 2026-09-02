"""Print row count, operated rate, and delay rate among operated flights."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "clean" / "flights.parquet"

df = pd.read_parquet(PARQUET)
print('Total rows: ', len(df), 'Operated rate: ', df["OPERATED"].mean(), 'Delay rate: ', df.loc[df["OPERATED"], "DELAYED"].mean())
