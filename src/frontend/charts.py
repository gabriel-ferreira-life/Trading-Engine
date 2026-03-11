# ─────────────────────────────────────────────
# charts.py
# Pure Plotly figure builders.
# No Streamlit imports — easy to test in isolation.
# ─────────────────────────────────────────────

import pandas as pd
import plotly.graph_objects as go

# Neutral layout that works with both Streamlit
# light and dark themes — no hardcoded colors.
PLOTLY_LAYOUT = dict(
    font=dict(family="sans-serif", size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
)


def build_equity_curves_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """
    Cumulative equity curves: Buy & Hold vs Strategy.

    Required columns : Asset_Equity, Strategy_Equity
    Index            : DatetimeIndex (or convertible)
    """
    idx = (
        df.index
        if isinstance(df.index, pd.DatetimeIndex)
        else pd.to_datetime(df.get("Date", df.index))
    )

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=idx, y=df["Asset_Equity"],
        name="Buy & Hold",
        mode="lines",
        line=dict(color="#f0a500", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=idx, y=df["Strategy_Equity"],
        name="Strategy",
        mode="lines",
        line=dict(color="#0068c9", width=2),
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=f"{ticker} — Equity Curves (cumulative return, start = 1.0)",
        xaxis_title="Date",
        yaxis_title="Cumulative Return",
        height=400,
    )
    return fig


def build_signals_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """
    Price + SMA overlays + buy/sell signal markers.

    Required columns : Adj Close (or Close), Position
    Optional columns : SMA_20, SMA_50
    Index            : DatetimeIndex (or convertible)
    """
    price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
    idx = (
        df.index
        if isinstance(df.index, pd.DatetimeIndex)
        else pd.to_datetime(df.get("Date", df.index))
    )

    changes  = df["Position"].diff()
    buy_df   = df[changes == 1]
    sell_df  = df[changes == -1]
    buy_idx  = (
        buy_df.index if isinstance(buy_df.index, pd.DatetimeIndex)
        else pd.to_datetime(buy_df.index)
    )
    sell_idx = (
        sell_df.index if isinstance(sell_df.index, pd.DatetimeIndex)
        else pd.to_datetime(sell_df.index)
    )

    fig = go.Figure()

    # Price
    fig.add_trace(go.Scatter(
        x=idx, y=df[price_col],
        name="Price", mode="lines",
        line=dict(color="gray", width=1.5),
        opacity=0.7,
    ))

    # Moving averages
    if "SMA_20" in df.columns:
        fig.add_trace(go.Scatter(
            x=idx, y=df["SMA_20"],
            name="SMA 20", mode="lines",
            line=dict(color="#0068c9", width=1.2, dash="dot"),
        ))
    if "SMA_50" in df.columns:
        fig.add_trace(go.Scatter(
            x=idx, y=df["SMA_50"],
            name="SMA 50", mode="lines",
            line=dict(color="#f0a500", width=1.2, dash="dot"),
        ))

    # Buy signals ▲
    if not buy_df.empty:
        fig.add_trace(go.Scatter(
            x=buy_idx, y=buy_df[price_col] * 0.985,
            name="Buy Signal", mode="markers",
            marker=dict(symbol="triangle-up", size=12, color="#29b09d"),
        ))

    # Sell signals ▼
    if not sell_df.empty:
        fig.add_trace(go.Scatter(
            x=sell_idx, y=sell_df[price_col] * 1.015,
            name="Sell Signal", mode="markers",
            marker=dict(symbol="triangle-down", size=12, color="#ff4b4b"),
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=f"{ticker} — Price, Moving Averages & Trade Signals",
        xaxis_title="Date",
        yaxis_title="Price",
        height=400,
    )
    return fig


def build_trade_metrics_chart(s: dict) -> go.Figure:
    """
    Bar chart: Avg Win / Avg Loss / Best Trade / Worst Trade.
    s: the summary dict from the API response.
    """
    categories = ["Avg Win", "Avg Loss", "Best Trade", "Worst Trade"]
    values = [
        s.get("Average_Win",  0) * 100,
        s.get("Average_Loss", 0) * 100,
        s.get("Best_Trade",   0) * 100,
        s.get("Worst_Trade",  0) * 100,
    ]
    colors = ["#29b09d" if v >= 0 else "#ff4b4b" for v in values]

    fig = go.Figure(go.Bar(
        x=categories, y=values,
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:+.2f}%" for v in values],
        textposition="outside",
    ))
    fig.add_hline(y=0, line_color="gray", line_width=1, line_dash="dot")

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title="Trade Distribution — per-trade returns",
        yaxis_title="Return (%)",
        yaxis_ticksuffix="%",
        height=350,
        showlegend=False,
    )
    return fig