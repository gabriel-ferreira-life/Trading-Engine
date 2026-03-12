import os
import pandas as pd
from backend.data_processor.fetcher_utils import get_fetch_range
from backend.data_processor.prices_fetcher import fetch_data, store_prices
from backend.data_processor.news_fetcher import fetch_news, store_news


DEFAULT_START = "2019-01-01"


def update_bronze_pipeline(ticker: str, interval: str = "daily", default_start: str = DEFAULT_START) -> None:
    """
    Brings all bronze-tier data sources up to date for a given ticker.
    Each source independently checks what it has and fetches only the delta.

    Adding a new data source (e.g. fundamentals, options flow):
        1. Write fetch_<source>() and store_<source>() in a new fetcher file
        2. Define its data_path and date_col below
        3. Call get_fetch_range() → fetch → store — same pattern as prices/news
    """
    print(f"\n[{ticker}] --- BRONZE PIPELINE ---")

    _update_prices(ticker, interval, default_start)
    _update_news(ticker, interval, default_start)


# ==========================================
# PRIVATE: Per-source update functions
# ==========================================

def _update_prices(ticker: str, interval: str, default_start: str) -> None:
    """Fetches and stores the OHLCV delta for a ticker."""
    data_path = f"../../../data/bronze/{ticker}/{interval}/data.parquet"
    fetch_start, is_current = get_fetch_range(data_path, date_col='Date', default_start=default_start)

    if is_current:
        print(f"[{ticker}] Prices are already up to date.")
        return

    print(f"[{ticker}] Fetching prices from {fetch_start}...")
    new_data = fetch_data(ticker, start_date=fetch_start)

    if new_data.empty:
        print(f"[{ticker}] No new price data available.")
        return

    store_prices(new_data, ticker, interval)


def _update_news(ticker: str, interval: str, default_start: str) -> None:
    """Fetches and stores the news delta for a ticker."""
    news_path = f"../../../data/bronze/{ticker}/{interval}/news.parquet"

    # News deduplicates on 'created_at' (timestamp-level), not 'Date' (day-level),
    # because multiple articles can land on the same calendar date.
    fetch_start, is_current = get_fetch_range(news_path, date_col='created_at', default_start=default_start)

    if (is_current) | (pd.to_datetime(fetch_start).date() == pd.Timestamp.today().date()):
        print(f"[{ticker}] News is already up to date.")
        return

    new_news = fetch_news(ticker, start_date=fetch_start)

    if new_news.empty:
        print(f"[{ticker}] No new news available.")
        return

    store_news(new_news, ticker, interval)