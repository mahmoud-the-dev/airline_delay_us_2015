from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw" / "Flight_Delays_Cleaned.csv"
CLEAN = ROOT / "clean" / "flights.parquet"

st.set_page_config(page_title="Airline Delay Intelligence", layout="wide")
st.title("Airline Delay Intelligence")
st.caption("US 2015 domestic flights · 50k extract · Streamlit + Plotly")

st.markdown(
    """
**Frozen source:** BTS / USDOT 2015, Kaggle pack
[US Flight Delays 2015 — Cleaned (50K)](https://www.kaggle.com/datasets/saurabhanand56/us-flight-delays-2015-cleaned-50k-ml-ready).
"""
)

if CLEAN.exists():
    st.success(f"Clean table found: `{CLEAN}`")
elif RAW.exists():
    st.warning(f"Raw CSV is in place (`{RAW.name}`). Run `python src/clean.py` to publish `clean/`.")
else:
    st.info(
        "Download `Flight_Delays_Cleaned.csv` into the `raw/` folder, then run `python src/clean.py`."
    )
