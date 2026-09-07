"""Person A: load raw CSV, engineer flags/buckets, write clean tables.

Run after Flight_Delays_Cleaned.csv is in ../raw/
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw" / "Flight_Delays_Cleaned.csv"
AIRPORT_LOOKUP = ROOT / "raw" / "lookups" / "BTS_2015_Airport_ID_IATA.xlsx"
CLEAN = ROOT / "clean"
IATA_RE = r"[A-Za-z]{3}"
BTS_ID_RE = r"\d{5}"


def load_bts_id_to_iata(path: Path) -> dict[str, str]:
    """First sheet of the 2015 BTS ID → IATA workbook (322 airports)."""
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}\nPut BTS_2015_Airport_ID_IATA.xlsx in raw/lookups/."
        )
    lu = pd.read_excel(path, sheet_name=0, dtype=str)
    lu.columns = [str(c).strip() for c in lu.columns]
    if "ID" not in lu.columns or "IATA" not in lu.columns:
        raise ValueError(f"Airport lookup must have ID and IATA columns, got {list(lu.columns)}")
    ids = lu["ID"].astype(str).str.strip()
    iata = lu["IATA"].astype(str).str.strip().str.upper()
    ok = ids.str.fullmatch(BTS_ID_RE) & iata.str.fullmatch(IATA_RE)
    return dict(zip(ids[ok], iata[ok]))


def remap_airport_column(series: pd.Series, id_to_iata: dict[str, str]) -> tuple[pd.Series, pd.Series]:
    """Leave 3-letter IATA; map 5-digit BTS IDs; keep unmatched IDs as-is."""
    s = series.astype(str).str.strip()
    is_id = s.str.fullmatch(BTS_ID_RE, na=False)
    mapped = s.map(id_to_iata)
    out = s.copy()
    hit = is_id & mapped.notna()
    out.loc[hit] = mapped.loc[hit]
    leftover = s[is_id & mapped.isna()]
    return out, leftover


def delay_risk_bands(df: pd.DataFrame) -> pd.DataFrame:
    """BQ5 lookup: operated flights, airline × weekday × time block, n≥30.

    Delay-rate bands are fixed cuts, not terciles: Low <15%, Medium 15–25%, High ≥25%.
    """
    ops = df.loc[df["OPERATED"]]
    g = (
        ops.groupby(["AIRLINE", "DAY_OF_WEEK", "TIME_BLOCK"], observed=True)
        .agg(
            AIRLINE_NAME=("AIRLINE_NAME", "first"),
            DOW_NAME=("DOW_NAME", "first"),
            n_flights=("DELAYED", "size"),
            delay_rate=("DELAYED", "mean"),
        )
        .reset_index()
    )
    g = g.loc[g["n_flights"] >= 30].copy()
    g["DELAY_RISK_BAND"] = pd.cut(
        g["delay_rate"],
        bins=[-float("inf"), 0.15, 0.25, float("inf")],
        labels=["Low", "Medium", "High"],
        right=False,
    )
    return g.sort_values(["AIRLINE", "DAY_OF_WEEK", "TIME_BLOCK"]).reset_index(drop=True)


def report_airport_leftovers(name: str, leftover: pd.Series) -> None:
    n_rows = int(len(leftover))
    n_ids = int(leftover.nunique())
    print(f"{name}: leftover rows={n_rows:,}  unique unmatched IDs={n_ids}")
    if n_ids:
        counts = leftover.value_counts()
        preview = ", ".join(f"{i}×{c}" for i, c in counts.head(10).items())
        print(f"  unmatched {name} IDs: {preview}")


def main() -> None:
    if not RAW.exists():
        raise FileNotFoundError(
            f"Missing {RAW}\nDownload Flight_Delays_Cleaned.csv from the Kaggle 50k pack into raw/."
        )
    df = pd.read_csv(RAW)

    df = df.drop_duplicates() # No Effect because no duplicates in the data.
    # Operated flag
    df["OPERATED"] = ~df["CANCELLED"] & ~df["DIVERTED"]
    # Delayed flag
    df["DELAYED"] = df["OPERATED"] & (df["ARRIVAL_DELAY"] >= 15)

    # Departure hour and time block (BQ3, BQ5)
    df["DEP_HOUR"] = (df["SCHEDULED_DEPARTURE"] // 100).clip(0, 23)
    df["TIME_BLOCK"] = pd.cut(
        df["DEP_HOUR"],
        bins=[-1, 5, 11, 16, 20, 23],
        labels=["Overnight", "Morning", "Afternoon", "Evening", "Night"],
    )

    #label Airline codes
    NAMES = {
        "WN": "Southwest", "DL": "Delta", "AA": "American", "OO": "SkyWest",
        "EV": "ExpressJet", "UA": "United", "MQ": "Envoy", "B6": "JetBlue",
        "US": "US Airways", "AS": "Alaska", "NK": "Spirit", "F9": "Frontier",
        "HA": "Hawaiian", "VX": "Virgin America",
    }
    df["AIRLINE_NAME"] = df["AIRLINE"].map(NAMES).fillna(df["AIRLINE"])

    # DAY_OF_WEEK is 1=Monday … 7=Sunday (2015-01-01 was Thursday = 4)
    jan1 = (df["YEAR"] == 2015) & (df["MONTH"] == 1) & (df["DAY"] == 1)
    if jan1.any() and not (df.loc[jan1, "DAY_OF_WEEK"] == 4).all():
        raise ValueError(
            "DAY_OF_WEEK convention mismatch: 2015-01-01 should be Thursday (4)"
        )
    DOW_NAMES = {
        1: "Monday",
        2: "Tuesday",
        3: "Wednesday",
        4: "Thursday",
        5: "Friday",
        6: "Saturday",
        7: "Sunday",
    }
    df["DOW_NAME"] = df["DAY_OF_WEEK"].map(DOW_NAMES)

    CANCEL_REASON_NAMES = {
        "A": "Carrier",
        "B": "Weather",
        "C": "NAS",
        "D": "Security",
    }
    df["CANCEL_REASON_NAME"] = (
        df["CANCELLATION_REASON"].map(CANCEL_REASON_NAMES).fillna("Not cancelled")
    )

    SEASONS = {
        12: "DJF",
        1: "DJF",
        2: "DJF",
        3: "MAM",
        4: "MAM",
        5: "MAM",
        6: "JJA",
        7: "JJA",
        8: "JJA",
        9: "SON",
        10: "SON",
        11: "SON",
    }
    df["SEASON"] = df["MONTH"].map(SEASONS)

    # October 2015 stores origin/dest as 5-digit BTS IDs; other months already use IATA.
    id_to_iata = load_bts_id_to_iata(AIRPORT_LOOKUP)
    df["ORIGIN_AIRPORT"], origin_left = remap_airport_column(df["ORIGIN_AIRPORT"], id_to_iata)
    df["DESTINATION_AIRPORT"], dest_left = remap_airport_column(
        df["DESTINATION_AIRPORT"], id_to_iata
    )
    df["ORIGIN_IS_IATA"] = df["ORIGIN_AIRPORT"].str.fullmatch(IATA_RE, na=False)
    df["DEST_IS_IATA"] = df["DESTINATION_AIRPORT"].str.fullmatch(IATA_RE, na=False)
    print(f"Airport ID->IATA lookup size={len(id_to_iata)}")
    report_airport_leftovers("ORIGIN_AIRPORT", origin_left)
    report_airport_leftovers("DESTINATION_AIRPORT", dest_left)
    n_skip_origin = int((~df["ORIGIN_IS_IATA"]).sum())
    n_skip_dest = int((~df["DEST_IS_IATA"]).sum())
    print(
        "Airport charts should drop unmatched IDs only "
        f"(origin skip={n_skip_origin:,}, dest skip={n_skip_dest:,}), not all of October."
    )

    CLEAN.mkdir(exist_ok=True)
    out = CLEAN / "flights.parquet"
    df.to_parquet(out, index=False)
    print(f"Wrote {out}  rows={len(df):,}  cols={df.shape[1]}")

    bands = delay_risk_bands(df)
    bands_out = CLEAN / "delay_risk_bands.parquet"
    bands.to_parquet(bands_out, index=False)
    print(
        f"Wrote {bands_out}  groups={len(bands):,}  "
        f"(operated only; n>=30; Low<15%, Medium 15-25%, High>=25%)"
    )


if __name__ == "__main__":
    main()
