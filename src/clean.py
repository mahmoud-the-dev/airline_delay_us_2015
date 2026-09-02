"""Person A: load raw CSV, engineer flags/buckets, write clean tables.

Run after Flight_Delays_Cleaned.csv is in ../raw/
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw" / "Flight_Delays_Cleaned.csv"
CLEAN = ROOT / "clean"


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

    #label Airline codes
    NAMES = {
        "WN": "Southwest", "DL": "Delta", "AA": "American", "OO": "SkyWest",
        "EV": "ExpressJet", "UA": "United", "MQ": "Envoy", "B6": "JetBlue",
        "US": "US Airways", "AS": "Alaska", "NK": "Spirit", "F9": "Frontier",
        "HA": "Hawaiian", "VX": "Virgin America",
    }
    df["AIRLINE_NAME"] = df["AIRLINE"].map(NAMES).fillna(df["AIRLINE"])

    CLEAN.mkdir(exist_ok=True)
    out = CLEAN / "flights.parquet"
    df.to_parquet(out, index=False)
    print(f"Wrote {out}  rows={len(df):,}  cols={df.shape[1]}")


if __name__ == "__main__":
    main()
