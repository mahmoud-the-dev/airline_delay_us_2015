"""Four-tab shell: shared parquet load, sidebar filters, KPI row, existing charts."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.metrics import (
    avg_delay_minutes,
    cancel_rate,
    delay_rate,
    delayed_operated,
    flights,
    operated,
    top_origins,
)
from dashboard.theme import PLOTLY_TEMPLATE

CLEAN = ROOT / "clean" / "flights.parquet"
MONTHS = list(range(1, 13))
HOURS = list(range(0, 24))

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
def load_flights(mtime: float) -> pd.DataFrame:
    df = pd.read_parquet(CLEAN)
    if "DEP_HOUR" not in df.columns:
        df = df.copy()
        df["DEP_HOUR"] = (
            pd.to_numeric(df["SCHEDULED_DEPARTURE"], errors="coerce") // 100
        ).clip(0, 23)
    return df


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


def render_kpis(filtered: pd.DataFrame) -> None:
    n_flights = flights(filtered)
    rate = delay_rate(filtered)
    avg_delay = avg_delay_minutes(filtered)
    cancels = cancel_rate(filtered)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Flights", f"{n_flights:,}")
    c2.metric("Delay rate", fmt_pct(rate))
    c3.metric("Avg delay minutes", fmt_minutes(avg_delay))
    c4.metric("Cancel rate", fmt_pct(cancels))


if not CLEAN.exists():
    st.error("Clean table not found. Run `python src/clean.py` to write `clean/flights.parquet`.")
    st.stop()

df = load_flights(CLEAN.stat().st_mtime)
all_airlines = sorted(df["AIRLINE_NAME"].dropna().unique().tolist())

if "airline_filter" not in st.session_state:
    st.session_state.airline_filter = all_airlines.copy()
if "month_filter" not in st.session_state:
    st.session_state.month_filter = MONTHS.copy()

with st.sidebar:
    st.header("Filters")
    if st.button("Reset", use_container_width=True):
        st.session_state.airline_filter = all_airlines.copy()
        st.session_state.month_filter = MONTHS.copy()
        st.rerun()
    selected_airlines = st.multiselect("Airlines", options=all_airlines, key="airline_filter")
    selected_months = st.multiselect("Months", options=MONTHS, key="month_filter")
    st.caption("Clearing a list shows no flights. Reset restores all airlines and months.")

filtered = df[
    df["AIRLINE_NAME"].isin(selected_airlines) & df["MONTH"].isin(selected_months)
]
ops = operated(filtered)

tab_overview, tab_causes, tab_time, tab_cancels = st.tabs(
    ["Overview", "Causes", "Time & risk", "Cancels vs delay"]
)

with tab_overview:
    render_kpis(filtered)

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

    overall_rate = delay_rate(filtered)
    if len(by_airline) and not pd.isna(overall_rate):
        vs_overall = by_airline.copy()
        vs_overall["vs_overall"] = vs_overall["DELAYED"] - overall_rate
        vs_overall = vs_overall.sort_values("vs_overall", ascending=False)
        fig_vs = px.bar(
            vs_overall,
            x="vs_overall",
            y="AIRLINE_NAME",
            orientation="h",
            template=PLOTLY_TEMPLATE,
            title="Delay rate minus overall (operated flights)",
        )
        fig_vs.update_yaxes(title="Airline", autorange="reversed")
        fig_vs.update_layout(
            xaxis=dict(tickformat=".1%", title="Delay rate − overall"),
            margin=dict(l=10, r=10, t=48, b=10),
        )
        fig_vs.add_vline(x=0, line_width=1, line_color="gray")
        st.plotly_chart(fig_vs, use_container_width=True)
        st.caption(
            "Positive is worse than the delay-rate card for the current filter. "
            "Same operated `DELAYED` mean as the airline bars."
        )

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

    st.subheader("Which origins?")
    origins = top_origins(filtered, n=15)
    origins_plot = origins.sort_values(
        ["delay_rate", "ORIGIN_AIRPORT"], ascending=[False, True], na_position="last"
    )
    fig_o = px.bar(
        origins_plot,
        x="delay_rate",
        y="ORIGIN_AIRPORT",
        orientation="h",
        hover_data={"flights": True, "delay_rate": ":.1%"},
        template=PLOTLY_TEMPLATE,
        title="Delay rate at top 15 origins (by flight count)",
    )
    apply_delay_rate_axis(fig_o, x_is_rate=True)
    fig_o.update_yaxes(title="Origin", autorange="reversed")
    fig_o.update_layout(margin=dict(l=10, r=10, t=48, b=10))
    st.plotly_chart(fig_o, use_container_width=True)
    st.caption(
        "Busiest 15 IATA origins in the current filter (`top_origins`). "
        "Delay rate is delayed ÷ operated at that airport. "
        "Numeric leftover BTS IDs are dropped from this chart only."
    )

    st.subheader("How long are delays?")
    delayed = delayed_operated(filtered)
    by_avg = (
        delayed.groupby("AIRLINE_NAME", observed=True)["ARRIVAL_DELAY"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig_d = px.bar(
        by_avg,
        x="ARRIVAL_DELAY",
        y="AIRLINE_NAME",
        orientation="h",
        template=PLOTLY_TEMPLATE,
        title="Avg delay minutes by airline (delayed operated flights)",
    )
    fig_d.update_yaxes(title="Airline", autorange="reversed")
    fig_d.update_layout(
        xaxis=dict(title="Avg delay minutes", tickformat=".1f"),
        margin=dict(l=10, r=10, t=48, b=10),
    )
    st.plotly_chart(fig_d, use_container_width=True)
    st.caption(
        "Same grain as the card: mean `ARRIVAL_DELAY` among delayed operated flights, not all flights."
    )

with tab_causes:
    render_kpis(filtered)

with tab_time:
    render_kpis(filtered)

    by_hour = ops.groupby("DEP_HOUR")["DELAYED"].mean().reindex(HOURS).rename("DELAYED").reset_index()
    fig_c = px.bar(
        by_hour,
        x="DEP_HOUR",
        y="DELAYED",
        template=PLOTLY_TEMPLATE,
        title="Delay rate by scheduled departure hour (operated flights)",
    )
    fig_c.update_layout(
        xaxis=dict(
            title="Scheduled departure hour",
            type="category",
            categoryarray=HOURS,
            categoryorder="array",
        ),
        yaxis=dict(tickformat=".1%", title="Delay rate"),
        margin=dict(l=10, r=10, t=48, b=10),
    )
    st.plotly_chart(fig_c, use_container_width=True)
    st.caption(
        "Hour is scheduled departure (`DEP_HOUR`, 0–23). Same grain as the cards: delayed ÷ operated. "
        "Overnight hours are thin, so treat 0–4% swings there as noise."
    )

with tab_cancels:
    render_kpis(filtered)
