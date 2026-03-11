import os 
import pandas as pd
from datetime import timedelta
from data_processor.prices_fetcher import fetch_data, store_data
from data_processor.news_fetcher import fetch_stock_news

def update_bronze_pipeline(ticker, interval="daily", default_start="2019-01-01"):
    """
    The main engine function that checks what we have, 
    fetches what we need, and stores it safely.
    """
    stage_process = "bronze"
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

    # Fetch news for the same date range as our price data
    fetch_stock_news(ticker, fetch_start, interval="daily")