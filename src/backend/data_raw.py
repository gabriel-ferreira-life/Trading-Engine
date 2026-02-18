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


# ==========================================
# MODULE 2: THE TIER 1 ORCHESTRATOR 
# ==========================================

def update_raw_pipeline(ticker, interval="daily", default_start="2020-01-01"):
    """
    The main engine function that checks what we have, 
    fetches what we need, and stores it safely.
    """
    stage_process = "raw"
    data_path = f"../../data/{stage_process}/{ticker}/{interval}/data.parquet"
    
    # Figure out what data we are missing
    if os.path.exists(data_path):
        existing_df = pd.read_parquet(data_path, engine='pyarrow')
        last_recorded_date = pd.to_datetime(existing_df['Date'].iloc[-1])
        
        # We need data starting the day AFTER our last record
        fetch_start = (last_recorded_date + timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"[{ticker}] Local data ends {last_recorded_date.strftime('%Y-%m-%d')}. Fetching from {fetch_start}...")
    else:
        fetch_start = default_start
        print(f"[{ticker}] No local data. Fetching full history from {fetch_start}...")

    # Prevent fetching if the "fetch_start" is tomorrow (we are already up to date!)
    if pd.to_datetime(fetch_start) > pd.Timestamp.today():
        print(f"[{ticker}] Data is already fully up to date.")
        return

    # Fetch the missing data
    new_data = fetch_data(ticker, start_date=fetch_start)
    
    # Store the data
    if not new_data.empty and len(new_data) > 0:
        store_data(new_data, stage_process, ticker, interval)
    else:
        print(f"[{ticker}] No new trading days to download from Yahoo Finance.")