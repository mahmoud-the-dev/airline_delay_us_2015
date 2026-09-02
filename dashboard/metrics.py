"""KPI functions. Names and definitions must match KPI_DICTIONARY.md."""

from __future__ import annotations

import pandas as pd

DELAY_MINUTES = 15


def flights(df: pd.DataFrame) -> int:
    return int(len(df))

def operated(df):
    return df[df["OPERATED"]]

def delay_rate(df) -> float:
    o = operated(df)
    if len(o) == 0:
        return float("nan")
    return float(o["DELAYED"].mean())

def avg_delay_minutes(df) -> float:
    d = operated(df)
    d = d[d["DELAYED"]]
    if len(d) == 0:
        return float("nan")
    return float(d["ARRIVAL_DELAY"].mean())

def cancel_rate(df: pd.DataFrame, cancelled_col: str = "CANCELLED") -> float:
    if cancelled_col not in df.columns or len(df) == 0:
        return float("nan")
    s = df[cancelled_col]
    if s.dtype == bool:
        return float(s.mean())
    return float((pd.to_numeric(s, errors="coerce").fillna(0) > 0).mean())
