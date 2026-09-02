"""PoC single page: airline filter, KPI cards, BQ1 delay-rate charts."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.metrics import avg_delay_minutes, delay_rate, flights, operated
from dashboard.theme import PLOTLY_TEMPLATE

CLEAN = ROOT / "clean" / "flights.parquet"
MONTHS = list(range(1, 13))

st.set_page_config(page_title="Airline Delay Intelligence", layout="wide")
st.title("Airline Delay Intelligence")
st.caption("US 2015 domestic flights · 50k extract · Streamlit + Plotly")
st.markdown(
    """
**Frozen source:** BTS / USDOT 2015, Kaggle pack
[US Flight Delays 2015 — Cleaned (50K)](https://www.kaggle.com/datasets/saurabhanand56/us-flight-delays-2015-cleaned-50k-ml-ready).
"""
)


@st.cache_data
def load_flights() -> pd.DataFrame:
    return pd.read_parquet(CLEAN)


def fmt_pct(value: float) -> str:
    if pd.isna(value):
        return "—"
    return f"{value:.1%}"


def fmt_minutes(value: float) -> str:
    if pd.isna(value):
        return "—"
    return f"{value:.1f} min"


def apply_delay_rate_axis(fig, *, x_is_rate: bool) -> None:
    axis = "xaxis" if x_is_rate else "yaxis"
    fig.update_layout({axis: dict(tickformat=".1%", title="Delay rate")})


if not CLEAN.exists():
    st.error("Clean table not found. Run `python src/clean.py` to write `clean/flights.parquet`.")
    st.stop()

df = load_flights()
all_airlines = sorted(df["AIRLINE_NAME"].dropna().unique().tolist())

if "airline_filter" not in st.session_state:
    st.session_state.airline_filter = all_airlines.copy()

with st.sidebar:
    st.header("Filters")
    if st.button("Reset", use_container_width=True):
        st.session_state.airline_filter = all_airlines.copy()
        st.rerun()
    selected = st.multiselect("Airlines", options=all_airlines, key="airline_filter")

filtered = df[df["AIRLINE_NAME"].isin(selected)]
n_flights = flights(filtered)
rate = delay_rate(filtered)
avg_delay = avg_delay_minutes(filtered)

c1, c2, c3 = st.columns(3)
c1.metric("Flights", f"{n_flights:,}")
c2.metric("Delay rate", fmt_pct(rate))
c3.metric("Avg delay minutes", fmt_minutes(avg_delay))

ops = operated(filtered)

st.subheader("Who is delayed?")
by_airline = (
    ops.groupby("AIRLINE_NAME", observed=True)["DELAYED"]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)
fig_a = px.bar(
    by_airline,
    x="DELAYED",
    y="AIRLINE_NAME",
    orientation="h",
    template=PLOTLY_TEMPLATE,
    title="Delay rate by airline (operated flights)",
)
apply_delay_rate_axis(fig_a, x_is_rate=True)
fig_a.update_yaxes(title="Airline", autorange="reversed")
fig_a.update_layout(margin=dict(l=10, r=10, t=48, b=10))
st.plotly_chart(fig_a, use_container_width=True)

st.subheader("When does delay rate move?")
by_month = ops.groupby("MONTH")["DELAYED"].mean().reindex(MONTHS).rename("DELAYED").reset_index()
fig_b = px.line(
    by_month,
    x="MONTH",
    y="DELAYED",
    markers=True,
    template=PLOTLY_TEMPLATE,
    title="Delay rate by month (operated flights)",
)
fig_b.update_traces(connectgaps=False)
fig_b.update_layout(
    xaxis=dict(title="Month", type="category", categoryarray=MONTHS, categoryorder="array"),
    yaxis=dict(tickformat=".1%", title="Delay rate"),
    margin=dict(l=10, r=10, t=48, b=10),
)
st.plotly_chart(fig_b, use_container_width=True)
