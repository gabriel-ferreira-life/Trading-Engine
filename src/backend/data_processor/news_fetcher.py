import pandas as pd
import os
import sys
import backend.config as config
from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest

ALPACA_API_KEY = config.ALPACA_API_KEY
ALPACA_SECRET_KEY = config.ALPACA_SECRET_KEY
ALPACA_BASE_URL = config.ALPACA_BASE_URL

def fetch_stock_news(ticker, start_date, end_date=None, interval="daily"):
    """Fetches historical news text and saves it to the Raw tier."""
    bronze_dir = f"../../../data/bronze/{ticker}/{interval}"
    os.makedirs(bronze_dir, exist_ok=True)
    news_path = f"{bronze_dir}/news.parquet"
    
    print(f"--- Fetching Raw News for {ticker} ---")
    
    if end_date is None:
        end_date = pd.Timestamp.today().strftime("%Y-%m-%d")

    client = NewsClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
    request_params = NewsRequest(symbols=ticker, start=start_date, end=end_date, limit=2000)
    
    try:
        news_data = client.get_news(request_params)
        df_news = news_data.df
    except Exception as e:
        print(f"[ERROR] Failed to fetch news: {e}")
        return
        
    if df_news.empty:
        print(f"[!] No news found for {ticker}.")
        return
        
    # Keep only the essential text data to save disk space
    df_clean = df_news[['headline', 'summary', 'created_at']].copy()
    
    # Save the raw text to the data lake
    df_clean.to_parquet(news_path, engine='pyarrow')
    print(f"[SUCCESS] Saved raw news to {news_path}")

if __name__ == "__main__":
    # Example usage
    fetch_stock_news(ticker="MSFT", start_date="2026-01-01", end_date="2026-03-09")