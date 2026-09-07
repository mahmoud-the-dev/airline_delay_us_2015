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
    CAUSE_COLS,
    avg_delay_minutes,
    cancel_rate,
    cause_minutes,
    cause_share,
    delay_rate,
    delayed_operated,
    flights,
    operated,
    top_origins,
)
from dashboard.theme import PLOTLY_TEMPLATE

CLEAN = ROOT / "clean" / "flights.parquet"
BANDS = ROOT / "clean" / "delay_risk_bands.parquet"
MONTHS = list(range(1, 13))
HOURS = list(range(0, 24))
DOW_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIME_BLOCK_ORDER = ["Overnight", "Morning", "Afternoon", "Evening", "Night"]
CAUSE_LABELS = {
    "AIRLINE_DELAY": "Carrier",
    "WEATHER_DELAY": "Weather",
    "AIR_SYSTEM_DELAY": "NAS",
    "SECURITY_DELAY": "Security",
    "LATE_AIRCRAFT_DELAY": "Late aircraft",
}
CAUSE_ORDER = [CAUSE_LABELS[c] for c in CAUSE_COLS]
CANCEL_REASON_ORDER = ["Carrier", "Weather", "NAS", "Security"]

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


@st.cache_data
def load_risk_bands(mtime: float) -> pd.DataFrame:
    return pd.read_parquet(BANDS)


def fmt_pct(value: float) -> str:
    if pd.isna(value):
        return "—"
    return f"{value:.1%}"


def fmt_minutes(value: float) -> str:
    if pd.isna(value):
        return "—"
    return f"{value:.1f} min"


def delay_rate_matrix(
    df: pd.DataFrame, row_col: str, col_col: str, row_order: list[str], col_order: list[str]
) -> pd.DataFrame:
    empty = pd.DataFrame(index=row_order, columns=col_order, dtype="float64")
    if len(df) == 0:
        return empty
    mat = (
        df.groupby([row_col, col_col], observed=True)["DELAYED"]
        .mean()
        .unstack(col_col)
    )
    return mat.reindex(index=row_order, columns=col_order)


def delay_rate_heatmap(mat: pd.DataFrame, title: str):
    fig = px.imshow(
        mat.astype("float64"),
        x=[str(c) for c in mat.columns],
        y=[str(i) for i in mat.index],
        color_continuous_scale="YlOrRd",
        aspect="auto",
        template=PLOTLY_TEMPLATE,
        title=title,
        labels={"color": "Delay rate"},
    )
    fig.update_layout(
        coloraxis_colorbar=dict(tickformat=".1%"),
        margin=dict(l=10, r=10, t=48, b=10),
        xaxis_title="",
        yaxis_title="",
    )
    fig.update_traces(hovertemplate="%{y} · %{x}<br>Delay rate=%{z:.1%}<extra></extra>")
    return fig


def delay_rate_category_bar(frame: pd.DataFrame, x_col: str, categories: list, title: str, x_title: str):
    fig = px.bar(
        frame,
        x=x_col,
        y="DELAYED",
        template=PLOTLY_TEMPLATE,
        title=title,
    )
    fig.update_layout(
        xaxis=dict(title=x_title, type="category", categoryarray=categories, categoryorder="array"),
        yaxis=dict(tickformat=".1%", title="Delay rate"),
        margin=dict(l=10, r=10, t=48, b=10),
    )
    return fig


def apply_delay_rate_axis(fig, *, x_is_rate: bool) -> None:
    axis = "xaxis" if x_is_rate else "yaxis"
    fig.update_layout({axis: dict(tickformat=".1%", title="Delay rate")})


def cause_long(df: pd.DataFrame) -> pd.DataFrame:
    """Share and minutes per cause. Empty when `cause_share` is all nan."""
    share = cause_share(df)
    mins = cause_minutes(df)
    out = pd.DataFrame(
        {
            "cause": CAUSE_ORDER,
            "share": [share[c] for c in CAUSE_COLS],
            "minutes": [mins[c] for c in CAUSE_COLS],
        }
    )
    if out["share"].isna().all():
        return out.iloc[0:0]
    return out


def cause_share_by_airline(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for airline, part in df.groupby("AIRLINE_NAME", observed=True):
        long = cause_long(part)
        if len(long) == 0:
            continue
        long = long.copy()
        long["AIRLINE_NAME"] = airline
        rows.append(long)
    if not rows:
        return pd.DataFrame(columns=["cause", "share", "minutes", "AIRLINE_NAME"])
    return pd.concat(rows, ignore_index=True)


def cancelled_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Same cancelled definition as `cancel_rate`."""
    if "CANCELLED" not in df.columns or len(df) == 0:
        return df.iloc[0:0]
    s = df["CANCELLED"]
    if s.dtype == bool:
        return df.loc[s]
    return df.loc[pd.to_numeric(s, errors="coerce").fillna(0) > 0]


def airline_delay_cancel(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for airline, part in df.groupby("AIRLINE_NAME", observed=True):
        rows.append(
            {
                "AIRLINE_NAME": airline,
                "flights": flights(part),
                "delay_rate": delay_rate(part),
                "cancel_rate": cancel_rate(part),
            }
        )
    if not rows:
        return pd.DataFrame(columns=["AIRLINE_NAME", "flights", "delay_rate", "cancel_rate"])
    return pd.DataFrame(rows)


def cancel_reason_share_by_airline(df: pd.DataFrame) -> pd.DataFrame:
    cancelled = cancelled_rows(df)
    if len(cancelled) == 0 or "CANCEL_REASON_NAME" not in cancelled.columns:
        return pd.DataFrame(columns=["AIRLINE_NAME", "reason", "share", "cancels"])
    reasons = cancelled.loc[cancelled["CANCEL_REASON_NAME"].isin(CANCEL_REASON_ORDER)]
    if len(reasons) == 0:
        return pd.DataFrame(columns=["AIRLINE_NAME", "reason", "share", "cancels"])
    counts = (
        reasons.groupby(["AIRLINE_NAME", "CANCEL_REASON_NAME"], observed=True)
        .size()
        .rename("cancels")
        .reset_index()
        .rename(columns={"CANCEL_REASON_NAME": "reason"})
    )
    totals = counts.groupby("AIRLINE_NAME")["cancels"].transform("sum")
    counts["share"] = counts["cancels"] / totals
    return counts


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
bands = load_risk_bands(BANDS.stat().st_mtime) if BANDS.exists() else None
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
bands_filtered = (
    bands[bands["AIRLINE_NAME"].isin(selected_airlines)] if bands is not None else None
)

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
    fig_o = px.bar(
        origins,
        x="delay_rate",
        y="ORIGIN_AIRPORT",
        orientation="h",
        text="flights",
        hover_data={"flights": True, "delay_rate": ":.1%"},
        template=PLOTLY_TEMPLATE,
        title="Delay rate at the 15 busiest origins",
    )
    apply_delay_rate_axis(fig_o, x_is_rate=True)
    fig_o.update_traces(texttemplate="%{text:,} flights", textposition="outside")
    fig_o.update_yaxes(title="Origin", autorange="reversed")
    fig_o.update_layout(margin=dict(l=10, r=10, t=48, b=10), uniformtext_minsize=8, uniformtext_mode="hide")
    st.plotly_chart(fig_o, use_container_width=True)
    st.caption(
        "Same 15 IATA origins as `top_origins`: busiest by flight count, not the worst delay rates. "
        "Bars stay in volume order (ATL first on the full extract). "
        "Delay rate is delayed ÷ operated at that airport. Numeric leftover BTS IDs are dropped from this chart only."
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

    st.subheader("What drives delay minutes?")
    by_cause_airline = cause_share_by_airline(filtered)
    overall_causes = cause_long(filtered)

    if len(by_cause_airline):
        airline_order = (
            by_cause_airline.groupby("AIRLINE_NAME")["minutes"].sum().sort_values(ascending=False).index.tolist()
        )
        fig_stack = px.bar(
            by_cause_airline,
            x="share",
            y="AIRLINE_NAME",
            color="cause",
            orientation="h",
            barmode="stack",
            category_orders={"AIRLINE_NAME": airline_order, "cause": CAUSE_ORDER},
            hover_data={"share": ":.1%", "minutes": ":.0f"},
            template=PLOTLY_TEMPLATE,
            title="Cause-minute share by airline",
        )
        fig_stack.update_yaxes(title="Airline", autorange="reversed")
        fig_stack.update_layout(
            xaxis=dict(tickformat=".1%", title="Cause share", range=[0, 1]),
            legend_title="Cause",
            margin=dict(l=10, r=10, t=48, b=10),
        )
        st.plotly_chart(fig_stack, use_container_width=True)

    if len(overall_causes):
        fig_pie = px.pie(
            overall_causes,
            names="cause",
            values="minutes",
            category_orders={"cause": CAUSE_ORDER},
            template=PLOTLY_TEMPLATE,
            title="Cause-minute share (overall)",
        )
        fig_pie.update_traces(
            textinfo="percent+label",
            hovertemplate="%{label}<br>Share=%{percent}<br>Minutes=%{value:,.0f}<extra></extra>",
        )
        fig_pie.update_layout(margin=dict(l=10, r=10, t=48, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

    st.caption("Causes exist only for arrival delay ≥ 15 min.")

with tab_time:
    render_kpis(filtered)

    st.subheader("When in the week?")
    by_dow = ops.groupby("DOW_NAME")["DELAYED"].mean().reindex(DOW_ORDER).rename("DELAYED").reset_index()
    by_block = (
        ops.groupby("TIME_BLOCK", observed=True)["DELAYED"]
        .mean()
        .reindex(TIME_BLOCK_ORDER)
        .rename("DELAYED")
        .reset_index()
    )
    col_dow, col_block = st.columns(2)
    with col_dow:
        st.plotly_chart(
            delay_rate_category_bar(
                by_dow,
                "DOW_NAME",
                DOW_ORDER,
                "Delay rate by weekday (operated flights)",
                "Weekday",
            ),
            use_container_width=True,
        )
    with col_block:
        st.plotly_chart(
            delay_rate_category_bar(
                by_block,
                "TIME_BLOCK",
                TIME_BLOCK_ORDER,
                "Delay rate by time block (operated flights)",
                "Time block",
            ),
            use_container_width=True,
        )

    heat = delay_rate_matrix(ops, "DOW_NAME", "TIME_BLOCK", DOW_ORDER, TIME_BLOCK_ORDER)
    st.plotly_chart(
        delay_rate_heatmap(heat, "Delay rate by weekday × time block (operated flights)"),
        use_container_width=True,
    )

    by_hour = ops.groupby("DEP_HOUR")["DELAYED"].mean().reindex(HOURS).rename("DELAYED").reset_index()
    st.plotly_chart(
        delay_rate_category_bar(
            by_hour,
            "DEP_HOUR",
            HOURS,
            "Delay rate by scheduled departure hour (operated flights)",
            "Scheduled departure hour",
        ),
        use_container_width=True,
    )
    st.caption(
        "Hour is scheduled departure (`DEP_HOUR`, 0–23). Same grain as the cards: delayed ÷ operated. "
        "Overnight hours are thin, so treat 0–4% swings there as noise. "
        "Time blocks are Overnight 0–5, Morning 6–11, Afternoon 12–16, Evening 17–20, Night 21–23."
    )

    st.subheader("Historical delay risk")
    if bands_filtered is None:
        st.info("Risk lookup not found. Run `python src/clean.py` to write `clean/delay_risk_bands.parquet`.")
    elif len(bands_filtered) == 0:
        st.caption("No n≥30 airline × weekday × time-block cells for the current airline filter.")
    else:
        band_view = bands_filtered[
            ["AIRLINE_NAME", "DOW_NAME", "TIME_BLOCK", "n_flights", "delay_rate", "DELAY_RISK_BAND"]
        ].copy()
        band_view["DOW_NAME"] = pd.Categorical(band_view["DOW_NAME"], DOW_ORDER, ordered=True)
        band_view["TIME_BLOCK"] = pd.Categorical(
            band_view["TIME_BLOCK"].astype(str), TIME_BLOCK_ORDER, ordered=True
        )
        band_view["DELAY_RISK_BAND"] = pd.Categorical(
            band_view["DELAY_RISK_BAND"].astype(str), ["High", "Medium", "Low"], ordered=True
        )
        band_view = band_view.sort_values(
            ["DELAY_RISK_BAND", "delay_rate", "AIRLINE_NAME"], ascending=[True, False, True]
        )
        band_view = band_view.rename(
            columns={
                "AIRLINE_NAME": "Airline",
                "DOW_NAME": "Weekday",
                "TIME_BLOCK": "Time block",
                "n_flights": "Flights",
                "delay_rate": "Delay rate",
                "DELAY_RISK_BAND": "Risk band",
            }
        )
        st.caption("Each row is one airline × weekday × time-block cell with at least 30 operated flights.")
        st.dataframe(
            band_view,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Delay rate": st.column_config.NumberColumn(format="%.1%"),
                "Flights": st.column_config.NumberColumn(format="%d"),
            },
        )
    st.caption(
        "Historical 2015 risk, not a prediction. "
        "Airline filter applies; month does not — the lookup is year-round airline × weekday × time-block cells with at least 30 operated flights. "
        "Low < 15%, Medium 15% to < 25%, High ≥ 25%."
    )

with tab_cancels:
    render_kpis(filtered)

    st.subheader("Who cancels?")
    by_airline_cd = airline_delay_cancel(filtered)
    if len(by_airline_cd):
        by_cancel = by_airline_cd.sort_values("cancel_rate", ascending=False)
        fig_cancel = px.bar(
            by_cancel,
            x="cancel_rate",
            y="AIRLINE_NAME",
            orientation="h",
            hover_data={"flights": True, "cancel_rate": ":.1%"},
            template=PLOTLY_TEMPLATE,
            title="Cancel rate by airline",
        )
        fig_cancel.update_yaxes(title="Airline", autorange="reversed")
        fig_cancel.update_layout(
            xaxis=dict(tickformat=".1%", title="Cancel rate"),
            margin=dict(l=10, r=10, t=48, b=10),
        )
        st.plotly_chart(fig_cancel, use_container_width=True)

        scatter = by_airline_cd.loc[by_airline_cd["flights"] > 0]
        fig_sc = px.scatter(
            scatter,
            x="delay_rate",
            y="cancel_rate",
            size="flights",
            hover_name="AIRLINE_NAME",
            hover_data={"flights": True, "delay_rate": ":.1%", "cancel_rate": ":.1%"},
            template=PLOTLY_TEMPLATE,
            title="Delay rate vs cancel rate",
            size_max=48,
        )
        fig_sc.update_layout(
            xaxis=dict(tickformat=".1%", title="Delay rate"),
            yaxis=dict(tickformat=".1%", title="Cancel rate"),
            margin=dict(l=10, r=10, t=48, b=10),
        )
        fig_sc.update_traces(marker=dict(sizemin=6, opacity=0.75))
        st.plotly_chart(fig_sc, use_container_width=True)
        st.caption(
            "Cancel rate is cancelled ÷ all flights (same as the card). "
            "Delay rate is delayed ÷ operated. Point size is flight count."
        )

    st.subheader("Busy origins")
    origin_cd = top_origins(filtered, n=15)
    if len(origin_cd):
        fig_oc = px.bar(
            origin_cd,
            x="cancel_rate",
            y="ORIGIN_AIRPORT",
            orientation="h",
            text="flights",
            hover_data={"flights": True, "cancel_rate": ":.1%", "delay_rate": ":.1%"},
            template=PLOTLY_TEMPLATE,
            title="Cancel rate at the 15 busiest origins",
        )
        fig_oc.update_traces(texttemplate="%{text:,} flights", textposition="outside")
        fig_oc.update_yaxes(title="Origin", autorange="reversed")
        fig_oc.update_layout(
            xaxis=dict(tickformat=".1%", title="Cancel rate"),
            margin=dict(l=10, r=10, t=48, b=10),
        )
        st.plotly_chart(fig_oc, use_container_width=True)

        fig_osc = px.scatter(
            origin_cd.loc[origin_cd["flights"] > 0],
            x="delay_rate",
            y="cancel_rate",
            size="flights",
            hover_name="ORIGIN_AIRPORT",
            hover_data={"flights": True, "delay_rate": ":.1%", "cancel_rate": ":.1%"},
            template=PLOTLY_TEMPLATE,
            title="Delay rate vs cancel rate (15 busiest origins)",
            size_max=48,
        )
        fig_osc.update_layout(
            xaxis=dict(tickformat=".1%", title="Delay rate"),
            yaxis=dict(tickformat=".1%", title="Cancel rate"),
            margin=dict(l=10, r=10, t=48, b=10),
        )
        fig_osc.update_traces(marker=dict(sizemin=6, opacity=0.75))
        st.plotly_chart(fig_osc, use_container_width=True)
        st.caption(
            "Same 15 IATA origins as Overview (`top_origins`), busiest by flight count. "
            "Cancel rate is cancelled ÷ all flights at that airport; delay rate is delayed ÷ operated. "
            "Numeric leftover BTS IDs are dropped from these charts only."
        )

    reason_mix = cancel_reason_share_by_airline(filtered)
    if len(reason_mix):
        st.subheader("Why were they cancelled?")
        airline_order = (
            reason_mix.groupby("AIRLINE_NAME")["cancels"].sum().sort_values(ascending=False).index.tolist()
        )
        fig_reason = px.bar(
            reason_mix,
            x="share",
            y="AIRLINE_NAME",
            color="reason",
            orientation="h",
            barmode="stack",
            category_orders={"AIRLINE_NAME": airline_order, "reason": CANCEL_REASON_ORDER},
            hover_data={"share": ":.1%", "cancels": True},
            template=PLOTLY_TEMPLATE,
            title="Cancel-reason mix by airline",
        )
        fig_reason.update_yaxes(title="Airline", autorange="reversed")
        fig_reason.update_layout(
            xaxis=dict(tickformat=".1%", title="Share of cancellations", range=[0, 1]),
            legend_title="Reason",
            margin=dict(l=10, r=10, t=48, b=10),
        )
        st.plotly_chart(fig_reason, use_container_width=True)
        overall_reasons = (
            cancelled_rows(filtered)
            .loc[lambda d: d["CANCEL_REASON_NAME"].isin(CANCEL_REASON_ORDER)]
            .groupby("CANCEL_REASON_NAME", observed=True)
            .size()
            .reindex(CANCEL_REASON_ORDER)
            .rename("cancels")
            .dropna()
            .reset_index()
            .rename(columns={"CANCEL_REASON_NAME": "reason"})
        )
        if len(overall_reasons):
            fig_reason_pie = px.pie(
                overall_reasons,
                names="reason",
                values="cancels",
                category_orders={"reason": CANCEL_REASON_ORDER},
                template=PLOTLY_TEMPLATE,
                title="Cancel-reason mix (overall)",
            )
            fig_reason_pie.update_traces(
                textinfo="percent+label",
                hovertemplate="%{label}<br>Share=%{percent}<br>Cancels=%{value:,}<extra></extra>",
            )
            fig_reason_pie.update_layout(margin=dict(l=10, r=10, t=48, b=10))
            st.plotly_chart(fig_reason_pie, use_container_width=True)
        st.caption("Cancel-reason mix is among cancelled flights only, not among all flights.")
