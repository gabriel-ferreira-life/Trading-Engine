import pandas as pd
import os
import yfinance as yf
from backend.data_processor.fetcher_utils import upsert_parquet

def fetch_data(ticker: str, start_date: str, end_date: str = None) -> pd.DataFrame:
    """Fetches historical OHLCV data from Yahoo Finance."""
    try:
        data = yf.download(ticker, start=start_date, end=end_date, auto_adjust=False)

        if data.empty:
            return pd.DataFrame()

        data.columns = data.columns.get_level_values(0)
        data.columns.name = None
        data = data.reset_index()
        data.insert(1, 'Ticker', ticker)
        return data
    
    except Exception as e:
        print(f"[ERROR] Failed to fetch price data for {ticker}: {e}")
        return pd.DataFrame()

def store_prices(data_df: pd.DataFrame, ticker: str, interval: str, stage: str = "bronze") -> None:
    """Upserts new OHLCV rows into the master parquet file."""
    data_path = f"../../../data/{stage}/{ticker}/{interval}/data.parquet"
    total_rows = upsert_parquet(data_df, data_path, date_col='Date')
    print(f"[{ticker}] Prices saved. Total rows in file: {total_rows}")