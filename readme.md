## Quantitative Trading Engine
An automated, full-stack quantitative trading backtester built on a Medallion Data Architecture. This engine features incremental data loading, calendar-aware indicator calculations, and a backtesting module.

## Directory Structure
```
trading_engine/
├── .venv
├── .gitignore
├── requirements.txt
├── readme.md
│
├── data/                 # Medallion Data Lake (Parquet)
│   ├── bronze/            # BRONZE: Original yfinance history
│   ├── silver/            # SILVER: Featured with RSI, MAs, MACD, and etc.
│   └── gold/              # GOLD: Backtest results and trade logs
│
└── src/
    ├── frontend/              # UI Dashboard
    │   ├── charts.py           # Frontend graphs
    │   └── app.py              # streamlit app
    │
    └── backend/                   # Core Engine
        ├── .env                     # API Keys
        ├── config.py                # Config
        ├── utils.py                 # Holiday/Crypto calendar routing
        ├── api.py                   # FastAPI 
        ├── engine_backtest.py       # Vectorized portfolio simulation & P&L
        ├── cli_demo.py              # Master Orchestrator & CLI
        └── backend/ 
            └── data_processor/ 
            │   ├── stock_prices_fetcher.py         # Fetches & upserts raw historical data
            │   ├── stock_news_fetcher.py           # Fetches & upserts historical news data
            │   ├── indicator_calculator.py         # Calculates indicators with lookback safety  
            │   └── data_eraser.py                  # Erases parquet caches
            │
            └── trading_strategy/ 
                ├── baseline.py                     # Alpha: RSI 35/65 Mean Reversion
                ├── tier1.py  
                └── tier2.py  
```

## Core Features
* **Incremental "Upsert" Data Loading:** Never downloads the same day twice. The engine reads the latest local Parquet file and fetches only the missing trading days from Yahoo Finance.

* **Asset-Class Aware Calendar Logic:** Automatically routes lookback periods based on the asset class. Skips weekends and US Federal holidays for equities (e.g., NVDA), but calculates true 24/7 lookbacks for crypto (e.g., BTC).

* **Resilient Parquet Schema:** Avoids MultiIndex corruption by flattening Yahoo Finance outputs, enforcing a strict column-based Date and Ticker schema on disk, and promoting the Date to a DatetimeIndex in RAM for time-series analysis.

* **Vectorized Backtesting:** Eliminates slow for loops. Uses pandas matrix math (shift, diff, cumprod) to execute simulated trades over decades of data in milliseconds.

* **Interactive CLI Dashboard:** Includes a live terminal menu to run backtests, view metrics, or wipe the data cache on the fly.

* **Visual Montages:** Automatically generates a side-by-side Matplotlib dashboard showing exact Buy/Sell execution arrows alongside the cumulative equity curve.
