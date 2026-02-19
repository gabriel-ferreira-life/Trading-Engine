## Quantitative Trading Engine
An automated, full-stack quantitative trading backtester built on a Medallion Data Architecture. This engine features incremental data loading, calendar-aware indicator calculations, and a backtesting module.

## Directory Structure
```
trading_engine/
│
├── data/                      # Medallion Data Lake (Parquet)
│   ├── raw/                   # 🥉 BRONZE: Untouched yfinance history
│   ├── features/              # 🥈 SILVER: Enriched with RSI, MAs, MACD
│   └── insights/              # 🥇 GOLD: Backtest results and trade logs
│
└── src/
    ├── frontend/              # (Planned) UI Dashboard
    └── backend/               # Core Engine
        ├── utils.py                 # Holiday/Crypto calendar routing
        ├── data_raw.py              # Fetches & upserts raw historical data
        ├── data_features.py         # Calculates indicators with lookback safety
        ├── data_eraser.py           # Erases parquet caches
        ├── strategy_baseline.py     # Alpha: RSI 35/65 Mean Reversion
        ├── engine_backtest.py       # Vectorized portfolio simulation & P&L
        └── engine_main.py           # Master Orchestrator & CLI
```

## Core Features
* **Incremental "Upsert" Data Loading:** Never downloads the same day twice. The engine reads the latest local Parquet file and fetches only the missing trading days from Yahoo Finance.

* **Asset-Class Aware Calendar Logic:** Automatically routes lookback periods based on the asset class. Skips weekends and US Federal holidays for equities (e.g., NVDA), but calculates true 24/7 lookbacks for crypto (e.g., BTC).

* **Resilient Parquet Schema:** Avoids MultiIndex corruption by flattening Yahoo Finance outputs, enforcing a strict column-based Date and Ticker schema on disk, and promoting the Date to a DatetimeIndex in RAM for time-series analysis.

* **Vectorized Backtesting:** Eliminates slow for loops. Uses pandas matrix math (shift, diff, cumprod) to execute simulated trades over decades of data in milliseconds.

* **Interactive CLI Dashboard:** Includes a live terminal menu to run backtests, view metrics, or wipe the data cache on the fly.

* **Visual Montages:** Automatically generates a side-by-side Matplotlib dashboard showing exact Buy/Sell execution arrows alongside the cumulative equity curve.