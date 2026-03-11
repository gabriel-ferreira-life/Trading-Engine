import json
from datetime import date

import pandas as pd
import requests
import streamlit as st

from charts import (
    build_equity_curves_chart,
    build_signals_chart,
    build_trade_metrics_chart,
)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
API_URL = "http://localhost:8000/api/v1/backtest"

st.set_page_config(
    page_title="Quant Backtest Engine",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("⬡ Quant Engine")
    st.caption("Systematic strategy evaluation")
    st.divider()

    ticker     = st.text_input("Ticker Symbol", value="MSFT", placeholder="AAPL, BTC, SPY…")
    strategy   = st.selectbox("Strategy", ["baseline", "tier_1"])
    interval   = st.selectbox("Interval", ["daily"]) # Pending: "1h", "15m"
    start_date = st.date_input("Start Date", value=date(2023, 1, 1))
    end_date   = st.date_input("End Date",   value=date.today())
    st.divider()

    run_button = st.button("▶  Run Backtest", type="primary", use_container_width=True)
    st.caption("POST → /api/v1/backtest")

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("Backtest Results")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if not run_button:
    st.info("Configure parameters in the sidebar and press **Run Backtest** to begin.")
    st.stop()

if not ticker:
    st.warning("Please enter a ticker symbol.")
    st.stop()

# ── API Call ──────────────────────────────────
with st.spinner(f"Running `{strategy}` strategy on `{ticker}`…"):
    payload = {
        "ticker":     ticker,
        "strategy":   strategy,
        "interval":   interval,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date":   end_date.strftime("%Y-%m-%d"),
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=120)
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to `{API_URL}`. Is your FastAPI server running?")
        st.stop()

    if response.status_code != 200:
        st.error(f"API Error ({response.status_code}): {response.json().get('detail', 'Unknown error.')}")
        st.stop()

    result_data = response.json()
    s = result_data.get("summary", {})

    # Load dataset parquet for time-series charts
    dataset_path = result_data.get("data_files", {}).get("dataset")
    df_dataset = None
    if dataset_path:
        try:
            df_dataset = pd.read_parquet(dataset_path)
            if "Date" in df_dataset.columns:
                df_dataset = df_dataset.set_index("Date")
            df_dataset.index = pd.to_datetime(df_dataset.index)
        except Exception as e:
            st.warning(f"Could not load dataset parquet: {e}")

# ── Run info ──────────────────────────────────
st.caption(
    f"**{s.get('Ticker')}** · {strategy.upper()} · {interval.upper()} · "
    f"{s.get('Start_Date')} → {s.get('End_Date')} · "
    f"Simulated on {s.get('Simulation_Date')}"
)
st.divider()

# ── Performance Scorecard ─────────────────────
st.subheader("Performance Scorecard")

# Row 1: the three headline return figures
col1, col2, col3 = st.columns(3)

bh    = s.get("Buy_Hold_Return", 0)
strat = s.get("Strategy_Return", 0)
delta = s.get("Performance_Delta", 0)

col1.metric(
    label="Buy & Hold Return",
    value=f"{bh * 100:.2f}%",
    help="Benchmark: buy at start, hold to end.",
)
col2.metric(
    label="Strategy Return",
    value=f"{strat * 100:.2f}%",
    delta=f"{delta * 100:.2f}% vs benchmark",
    delta_color="normal",
    help="Cumulative return of the backtest strategy.",
)
col3.metric(
    label="Performance Delta",
    value=f"{delta * 100:.2f}%",
    delta="outperform" if delta >= 0 else "underperform",
    delta_color="normal" if delta >= 0 else "inverse",
    help="Strategy return minus buy-and-hold return.",
)

st.divider()

# Row 2: trade-level statistics
col4, col5, col6, col7, col8 = st.columns(5)

wr     = s.get("Win_Rate", 0)
trades = s.get("Total_Trades_Taken", 0)
tdays  = s.get("Total_Trading_Days", 0)

col4.metric("Win Rate",    f"{wr * 100:.1f}%", help="Percentage of trades that closed in profit.")
col5.metric("Total Trades", str(trades),        help=f"Executed over {tdays:,} trading days.")
col6.metric("Best Trade",  f"{s.get('Best_Trade',  0) * 100:.2f}%", help="Highest single-trade return.")
col7.metric("Worst Trade", f"{s.get('Worst_Trade', 0) * 100:.2f}%", help="Lowest single-trade return.")
col8.metric(
    "Avg Win / Loss",
    f"{s.get('Average_Win', 0)*100:.2f}% / {s.get('Average_Loss', 0)*100:.2f}%",
    help="Average return on winning vs losing trades.",
)

st.divider()

# Row 3: risk metrics
col9, col10, *_ = st.columns(5)

col9.metric(
    "Max Drawdown",
    f"{s.get('Max_Drawdown', 0) * 100:.2f}%",
    help="Largest peak-to-trough decline during the backtest period.",
)
col10.metric(
    "Sharpe Ratio",
    f"{s.get('Sharpe_Ratio', 0):.4f}",
    help="Risk-adjusted return. Above 1.0 is generally considered good.",
)

st.divider()

# ── Time Series Charts ────────────────────────
st.subheader("Time Series Analysis")

if df_dataset is not None:
    st.plotly_chart(
        build_equity_curves_chart(df_dataset, ticker),
        use_container_width=True,
        config={"displayModeBar": False},
    )
    st.plotly_chart(
        build_signals_chart(df_dataset, ticker),
        use_container_width=True,
        config={"displayModeBar": False},
    )
else:
    st.info("Equity curve and signal charts are unavailable — the dataset parquet could not be loaded.")

st.plotly_chart(
    build_trade_metrics_chart(s),
    use_container_width=True,
    config={"displayModeBar": False},
)

# ── Raw API Response ──────────────────────────
with st.expander("Raw API Response"):
    st.json(result_data)