"""KPI functions. Names and definitions must match KPI_DICTIONARY.md."""

from __future__ import annotations

import pandas as pd

DELAY_MINUTES = 15
CAUSE_COLS = [
    "AIRLINE_DELAY",
    "WEATHER_DELAY",
    "AIR_SYSTEM_DELAY",
    "SECURITY_DELAY",
    "LATE_AIRCRAFT_DELAY",
]


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


def delayed_operated(df: pd.DataFrame) -> pd.DataFrame:
    o = operated(df)
    return o[o["DELAYED"]]


def delayed_count(df: pd.DataFrame) -> int:
    return int(delayed_operated(df).shape[0])


def total_delay_minutes(df: pd.DataFrame) -> float:
    d = delayed_operated(df)
    if len(d) == 0:
        return 0.0
    return float(d["ARRIVAL_DELAY"].sum())


def divert_rate(df: pd.DataFrame, diverted_col: str = "DIVERTED") -> float:
    if diverted_col not in df.columns or len(df) == 0:
        return float("nan")
    s = df[diverted_col]
    if s.dtype == bool:
        return float(s.mean())
    return float((pd.to_numeric(s, errors="coerce").fillna(0) > 0).mean())


def cause_minutes(df: pd.DataFrame) -> pd.Series:
    d = delayed_operated(df)
    if len(d) == 0:
        return pd.Series(0.0, index=CAUSE_COLS, dtype="float64")
    return d[CAUSE_COLS].sum(numeric_only=True).reindex(CAUSE_COLS).astype("float64")


def cause_share(df: pd.DataFrame) -> pd.Series:
    mins = cause_minutes(df)
    total = float(mins.sum())
    if total == 0:
        return pd.Series(float("nan"), index=CAUSE_COLS, dtype="float64")
    return (mins / total).astype("float64")


def top_origins(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """Rank IATA origins by flight count. Numeric leftover IDs are excluded."""
    iata = iata_airports(df, "ORIGIN_AIRPORT")
    empty = pd.DataFrame(columns=["ORIGIN_AIRPORT", "flights", "delay_rate", "cancel_rate"])
    if len(iata) == 0:
        return empty

    flights_n = iata.groupby("ORIGIN_AIRPORT", observed=True).size().rename("flights")
    ops = operated(iata)
    delay = (
        ops.groupby("ORIGIN_AIRPORT", observed=True)["DELAYED"].mean().rename("delay_rate")
        if len(ops)
        else pd.Series(dtype="float64", name="delay_rate")
    )
    if "CANCELLED" in iata.columns:
        cancelled = iata["CANCELLED"]
        if cancelled.dtype == bool:
            cancel = cancelled
        else:
            cancel = pd.to_numeric(cancelled, errors="coerce").fillna(0) > 0
        cancel_by = (
            cancel.groupby(iata["ORIGIN_AIRPORT"], observed=True).mean().rename("cancel_rate")
        )
    else:
        cancel_by = pd.Series(dtype="float64", name="cancel_rate")

    out = (
        pd.concat([flights_n, delay, cancel_by], axis=1)
        .reset_index()
        .rename(columns={"index": "ORIGIN_AIRPORT"})
    )
    out["flights"] = out["flights"].fillna(0).astype(int)
    return out.sort_values(["flights", "ORIGIN_AIRPORT"], ascending=[False, True]).head(n).reset_index(drop=True)
