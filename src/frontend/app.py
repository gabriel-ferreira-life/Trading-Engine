import pandas as pd
import requests
import streamlit as st

from charts import build_equity_curves_chart, build_signals_chart

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
API_URL = "http://localhost:8000/api/v1/compare"

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
    interval   = st.selectbox("Interval", ["daily"])
    start_date = st.date_input("Start Date", value=pd.Timestamp("2023-01-01"))
    end_date   = st.date_input("End Date",   value=pd.Timestamp.today())
    st.divider()

    run_button = st.button("▶  Run All Strategies", type="primary", use_container_width=True)
    st.caption("POST → /api/v1/compare")

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.title("Strategy Comparison")

if not run_button:
    st.info("Configure parameters in the sidebar and press **Run All Strategies** to begin.")
    st.stop()

if not ticker:
    st.warning("Please enter a ticker symbol.")
    st.stop()

# ─────────────────────────────────────────────
# API CALL
# ─────────────────────────────────────────────
with st.spinner(f"Running all strategies on `{ticker.upper()}`…"):
    payload = {
        "ticker":     ticker.upper(),
        "interval":   interval,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date":   end_date.strftime("%Y-%m-%d"),
    }
    try:
        response = requests.post(API_URL, json=payload, timeout=300)
    except requests.exceptions.ConnectionError:
        st.error(f"Could not connect to `{API_URL}`. Is the FastAPI server running?")
        st.stop()

    if response.status_code != 200:
        st.error(f"API Error ({response.status_code}): {response.json().get('detail', 'Unknown error.')}")
        st.stop()

    result_data    = response.json()
    strategies     = result_data.get("strategies", {})
    strategy_names = list(strategies.keys())

# ─────────────────────────────────────────────
# LOAD PARQUET DATASETS
# ─────────────────────────────────────────────
strategy_dfs = {}
for name, data in strategies.items():
    path = data.get("data_files", {}).get("dataset")
    if path:
        try:
            df = pd.read_parquet(path)
            if "Date" in df.columns:
                df = df.set_index("Date")
            df.index = pd.to_datetime(df.index)
            strategy_dfs[name] = df
        except Exception as e:
            st.warning(f"Could not load dataset for `{name}`: {e}")

# ─────────────────────────────────────────────
# RUN INFO BAR
# ─────────────────────────────────────────────
first_summary = strategies[strategy_names[0]]["summary"] if strategy_names else {}
st.caption(
    f"**{ticker.upper()}** · {interval.upper()} · "
    f"{first_summary.get('Start_Date', '')} → {first_summary.get('End_Date', '')} · "
    f"Simulated on {first_summary.get('Simulation_Date', '')} · "
    f"{len(strategy_names)} strategies compared"
)
st.divider()

# ─────────────────────────────────────────────
# SECTION 1 — PERFORMANCE SCORECARD
# ─────────────────────────────────────────────
st.subheader("Performance Scorecard")

METRICS_DISPLAY = [
    ("Strategy Return",   "Strategy_Return",   "{:.2%}"),
    ("Buy & Hold Return", "Buy_Hold_Return",    "{:.2%}"),
    ("Performance Delta", "Performance_Delta",  "{:.2%}"),
    ("Sharpe Ratio",      "Sharpe_Ratio",       "{:.4f}"),
    ("Win Rate",          "Win_Rate",           "{:.1%}"),
    ("Max Drawdown",      "Max_Drawdown",       "{:.2%}"),
    ("Total Trades",      "Total_Trades_Taken", "{:.0f}"),
    ("Best Trade",        "Best_Trade",         "{:.2%}"),
    ("Worst Trade",       "Worst_Trade",        "{:.2%}"),
    ("Avg Win",           "Average_Win",        "{:.2%}"),
    ("Avg Loss",          "Average_Loss",       "{:.2%}"),
]

COLORED_KEYS = {
    "Strategy_Return", "Performance_Delta",
    "Best_Trade", "Worst_Trade", "Average_Win", "Average_Loss",
}

cols = st.columns(len(strategy_names))
for col, name in zip(cols, strategy_names):
    s = strategies[name]["summary"]
    col.markdown(f"### {name.replace('_', ' ').title()}")
    for display_name, key, fmt in METRICS_DISPLAY:
        val = s.get(key)
        if val is not None:
            formatted = fmt.format(val)
            if key in COLORED_KEYS:
                color = "green" if val >= 0 else "red"
                col.markdown(f"**{display_name}:** :{color}[{formatted}]")
            else:
                col.markdown(f"**{display_name}:** {formatted}")

st.divider()

# ─────────────────────────────────────────────
# SECTION 2 — EQUITY CURVES
# ─────────────────────────────────────────────
st.subheader("Equity Curves")

if strategy_dfs:
    st.plotly_chart(
        build_equity_curves_chart(strategy_dfs, ticker.upper()),
        use_container_width=True,
        config={"displayModeBar": False},
    )
else:
    st.info("No dataset files could be loaded for charting.")

st.divider()

# ─────────────────────────────────────────────
# SECTION 3 — SIGNALS  (one chart per strategy)
# ─────────────────────────────────────────────
st.subheader("Signals")

if not strategy_dfs:
    st.info("No dataset files could be loaded for signal charts.")
else:
    for name, df in strategy_dfs.items():
        st.markdown(f"##### {name.replace('_', ' ').title()}")
        st.plotly_chart(
            build_signals_chart(df, ticker.upper(), strategy_name=name),
            use_container_width=True,
            config={"displayModeBar": False},
        )

with st.expander("Raw API Response"):
    st.json(result_data)