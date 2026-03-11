import pandas as pd
import numpy as np
import os
import yfinance as yf
from datetime import datetime, timedelta

# ==========================================
# MODULE 1: DATA I/O (Fetch & Store)
# ==========================================

def fetch_data(ticker, start_date, end_date=None):
    """Fetches historical stock data from Yahoo Finance."""
    try:
        data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)
        data.columns = data.columns.get_level_values(0)
        data.columns.name = None
        data = data.reset_index()
        data.insert(1, 'Ticker', ticker)
        return data
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()

def store_data(data_df, stage_process, ticker, interval):
    """Upserts new data into the master parquet file."""
    data_dir = f"../../data/{stage_process}/{ticker}/{interval}"
    data_path = f"{data_dir}/data.parquet"
    
    os.makedirs(data_dir, exist_ok=True)

    if os.path.exists(data_path):
        existing_df = pd.read_parquet(data_path, engine='pyarrow')
        combined_df = pd.concat([existing_df, data_df])
        combined_df = combined_df.drop_duplicates(subset=['Date'], keep='last')
        combined_df = combined_df.sort_values(by='Date')
        combined_df.to_parquet(data_path, index=False, engine='pyarrow')
        print(f"[{ticker}] Appended data. Master file total rows: {len(combined_df)}")
    else:
        data_df.sort_index().to_parquet(data_path, index=False, engine='pyarrow')
        print(f"[{ticker}] Created new master file at: {data_path}")