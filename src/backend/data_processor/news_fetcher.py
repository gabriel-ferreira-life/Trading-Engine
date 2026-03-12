import pandas as pd
import os
import backend.config as config
from alpaca.data.historical.news import NewsClient
from alpaca.data.requests import NewsRequest
from backend.data_processor.fetcher_utils import upsert_parquet

ALPACA_API_KEY = config.ALPACA_API_KEY
ALPACA_SECRET_KEY = config.ALPACA_SECRET_KEY

def fetch_news(ticker: str, start_date: str, end_date: str = None) -> pd.DataFrame:
    """Fetches news headlines from Alpaca for a given date range."""
    if end_date is None:
        end_date = pd.Timestamp.today().strftime("%Y-%m-%d")

    print(f"[{ticker}] Fetching news from {start_date} to {end_date}...")

    try:
        client = NewsClient(ALPACA_API_KEY, ALPACA_SECRET_KEY, raw_data=True)
        request_params = NewsRequest(
            symbols=ticker,
            start=start_date,
            end=end_date,
            limit=2000
        )
        news_data = client.get_news(request_params)
        news_list = news_data.get('news', [])

        if len(news_list) == 0:
            print(f"[{ticker}] No news found for this date range.")
            return pd.DataFrame()
        else:
            df_news = pd.DataFrame(news_list)

    except Exception as e:
        print(f"[ERROR] Failed to fetch news for {ticker}: {e}")
        return pd.DataFrame()



    # Normalise to a clean daily date for deduplication and merging
    df_clean = df_news[['id', 'headline', 'summary', 'created_at']].copy()
    df_clean.insert(1, 'Ticker', ticker)
    df_clean.insert(2, 'Date',
                    pd.to_datetime(df_clean['created_at']).dt.tz_localize(None).dt.normalize()
                    )

    return df_clean


def store_news(news_df: pd.DataFrame, ticker: str, interval: str, stage: str = "bronze") -> None:
    """
    Upserts new news rows into the master news parquet file.

    Note: News deduplicates on 'created_at' (not 'Date') because multiple
    articles can share the same calendar date.
    """
    news_path = f"../../../data/{stage}/{ticker}/{interval}/news.parquet"
    total_rows = upsert_parquet(news_df, news_path, date_col='created_at')
    print(f"[{ticker}] News saved. Total rows in file: {total_rows}")