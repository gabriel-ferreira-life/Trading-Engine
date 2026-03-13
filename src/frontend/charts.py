# ─────────────────────────────────────────────
# charts.py
# Pure Plotly figure builders — no Streamlit imports.
# ─────────────────────────────────────────────

import pandas as pd
import plotly.graph_objects as go

PLOTLY_LAYOUT = dict(
    font=dict(family="sans-serif", size=12),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
)

# Distinct palette for strategy lines — extend if you add more strategies
STRATEGY_COLORS = [
    "#0068c9",  # blue
    "#29b09d",  # teal
    "#9b59b6",  # purple
    "#e67e22",  # orange
    "#e74c3c",  # red
]


def build_equity_curves_chart(strategy_dfs: dict, ticker: str) -> go.Figure:
    """
    Overlaid cumulative equity curves for N strategies + one Buy & Hold baseline.

    Args:
        strategy_dfs : dict[strategy_name -> DataFrame]
                       Each DataFrame must have 'Asset_Equity' and 'Strategy_Equity'
                       columns and a DatetimeIndex (or 'Date' column).
        ticker       : Used in the chart title.
    """
    fig = go.Figure()

    bh_added = False  # Buy & Hold is identical across strategies — draw it once

    for i, (strategy_name, df) in enumerate(strategy_dfs.items()):
        idx = (
            df.index if isinstance(df.index, pd.DatetimeIndex)
            else pd.to_datetime(df.get("Date", df.index))
        )
        color = STRATEGY_COLORS[i % len(STRATEGY_COLORS)]

        # Buy & Hold — drawn once from the first available df
        if not bh_added and "Asset_Equity" in df.columns:
            fig.add_trace(go.Scatter(
                x=idx, y=df["Asset_Equity"],
                name="Buy & Hold",
                mode="lines",
                line=dict(color="#f0a500", width=2, dash="dot"),
            ))
            bh_added = True

        # Strategy equity curve
        if "Strategy_Equity" in df.columns:
            fig.add_trace(go.Scatter(
                x=idx, y=df["Strategy_Equity"],
                name=strategy_name.replace("_", " ").title(),
                mode="lines",
                line=dict(color=color, width=2),
            ))

    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=f"{ticker} — Strategy Comparison (cumulative return, start = 1.0)",
        xaxis_title="Date",
        yaxis_title="Cumulative Return",
        height=450,
    )
    return fig


def build_signals_chart(df: pd.DataFrame, ticker: str, strategy_name: str = "") -> go.Figure:
    """
    Price + SMA overlays + buy/sell signal markers for a single strategy.

    Required columns : Adj Close (or Close), Position
    Optional columns : SMA_20, SMA_50
    """
    price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
    idx = (
        df.index if isinstance(df.index, pd.DatetimeIndex)
        else pd.to_datetime(df.get("Date", df.index))
    )

    changes  = df["Position"].diff()
    buy_df   = df[changes == 1]
    sell_df  = df[changes == -1]
    buy_idx  = buy_df.index  if isinstance(buy_df.index,  pd.DatetimeIndex) else pd.to_datetime(buy_df.index)
    sell_idx = sell_df.index if isinstance(sell_df.index, pd.DatetimeIndex) else pd.to_datetime(sell_df.index)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=idx, y=df[price_col],
        name="Price", mode="lines",
        line=dict(color="gray", width=1.5), opacity=0.7,
    ))

    if "SMA_20" in df.columns:
        fig.add_trace(go.Scatter(
            x=idx, y=df["SMA_20"], name="SMA 20", mode="lines",
            line=dict(color="#0068c9", width=1.2, dash="dot"),
        ))
    if "SMA_50" in df.columns:
        fig.add_trace(go.Scatter(
            x=idx, y=df["SMA_50"], name="SMA 50", mode="lines",
            line=dict(color="#f0a500", width=1.2, dash="dot"),
        ))

    if not buy_df.empty:
        fig.add_trace(go.Scatter(
            x=buy_idx, y=buy_df[price_col] * 0.985,
            name="Buy", mode="markers",
            marker=dict(symbol="triangle-up", size=12, color="#29b09d"),
        ))
    if not sell_df.empty:
        fig.add_trace(go.Scatter(
            x=sell_idx, y=sell_df[price_col] * 1.015,
            name="Sell", mode="markers",
            marker=dict(symbol="triangle-down", size=12, color="#ff4b4b"),
        ))

    label = strategy_name.replace("_", " ").title()
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=f"{ticker} — {label} · Price, MAs & Trade Signals",
        xaxis_title="Date",
        yaxis_title="Price",
        height=400,
    )
    return fig