"""KPI functions. Names and definitions must match KPI_DICTIONARY.md."""

from __future__ import annotations

import pandas as pd

DELAY_MINUTES = 15


def flights(df: pd.DataFrame) -> int:
    return int(len(df))

def operated(df):
    return df[df["OPERATED"]]


def iata_airports(df: pd.DataFrame, airport_col: str = "ORIGIN_AIRPORT") -> pd.DataFrame:
    """Keep IATA-coded airport rows. Unmapped BTS IDs stay in the extract for other views."""
    flag = "ORIGIN_IS_IATA" if airport_col == "ORIGIN_AIRPORT" else "DEST_IS_IATA"
    if flag in df.columns:
        return df.loc[df[flag]]
    codes = df[airport_col].astype(str)
    return df.loc[codes.str.fullmatch(r"[A-Za-z]{3}", na=False)]

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
