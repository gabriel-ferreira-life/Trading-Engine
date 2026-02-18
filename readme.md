trading_engine/
│
├── data/                      # Your Medallion Data Lake
│   ├── raw/                   # (Bronze)
│   ├── features/              # (Silver)
│   └── insights/              # (Gold)
│
└── src/
    ├── frontend/              # UI (Streamlit, React, etc.)
    │
    └── backend/               # The Trading Engine
        ├── utils.py           # calculate_lookback_date()
        ├── tier1_raw.py       # fetch_data() and store_data()
        ├── tier2_features.py  # RSI math and feature upserts
        ├── tier3_backtest.py  # Trading logic and P&L math
        └── engine_main.py     # Master orchestrator