import os
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)
from backend.utils import calculate_lookback_date
from backend.data_processor.indicators import apply_indicators
from backend.data_processor.sentiment import compute_sentiment_feature


def _merge_sentiment(processing_df: pd.DataFrame, ticker: str, interval: str, since_date=None) -> pd.DataFrame:
    """
    Scores and merges sentiment into processing_df.
    Extracted as a helper so both the normal path and the schema-backfill
    path can call it without duplicating logic.
    """
    sentiment_df = compute_sentiment_feature(ticker, interval, since_date=since_date)
    processing_df = processing_df.join(sentiment_df, how='left')
    processing_df['Sentiment'] = processing_df['Sentiment'].ffill().fillna(0.0)
    return processing_df


def update_silver_pipeline(ticker: str, interval: str = "daily", lookback_days: int = 60) -> None:
    """
    Reads bronze data, calculates indicators with lookback-safe priming,
    scores sentiment (delta only), and upserts into the silver data lake.
    """
    bronze_path = f"../../../data/bronze/{ticker}/{interval}/data.parquet"
    silver_dir  = f"../../../data/silver/{ticker}/{interval}"
    silver_path = f"{silver_dir}/data.parquet"

    os.makedirs(silver_dir, exist_ok=True)

    if not os.path.exists(bronze_path):
        print(f"[{ticker}] Bronze data not found at {bronze_path}. Run bronze pipeline first.")
        return

    raw_df = pd.read_parquet(bronze_path, engine='pyarrow')
    raw_df['Date'] = pd.to_datetime(raw_df['Date'])

    # ── INCREMENTAL PATH ───────────────────────────────────────────────────────
    if os.path.exists(silver_path):
        features_df = pd.read_parquet(silver_path, engine='pyarrow')
        features_df['Date'] = pd.to_datetime(features_df['Date'])
        last_feature_date = features_df['Date'].iloc[-1]

        # Calculate the priming start date, accounting for crypto vs equity calendars
        prime_date, asset_class = calculate_lookback_date(ticker, last_feature_date, lookback_days)
        print(f"[{ticker}] ({asset_class}) Updating features from {prime_date.strftime('%Y-%m-%d')}...")

        processing_df = raw_df[raw_df['Date'] >= prime_date].copy()
        processing_df = apply_indicators(processing_df)

        # ── SCHEMA CHANGE DETECTION ────────────────────────────────────────────
        # If indicators added new columns, backfill the entire history and overwrite
        SENTIMENT_COLS = {'Sentiment'}
        if set(processing_df.columns) - SENTIMENT_COLS != set(features_df.columns) - SENTIMENT_COLS:
            print(f"[{ticker}] Schema change detected. Backfilling full history...")
            processing_df = apply_indicators(raw_df.copy())

            # Sentiment: score everything since no existing silver scores are valid
            processing_df = _merge_sentiment(processing_df, ticker, interval, since_date=None)

            combined_df = processing_df.dropna(subset=['RSI'])

        else:
            # Normal incremental: only score sentiment for genuinely new dates
            processing_df = _merge_sentiment(processing_df, ticker, interval, since_date=last_feature_date)

            new_features = processing_df[processing_df['Date'] > last_feature_date]
            combined_df = pd.concat([features_df, new_features])

    # ── FIRST RUN PATH ─────────────────────────────────────────────────────────
    else:
        print(f"[{ticker}] No existing silver data. Calculating full history...")
        processing_df = apply_indicators(raw_df.copy())
        processing_df = _merge_sentiment(processing_df, ticker, interval, since_date=None)

        # Drop NaN rows produced by the indicator warmup window (e.g. first 22 days for RSI)
        combined_df = processing_df.dropna(subset=['RSI'])

    # ── SAVE ───────────────────────────────────────────────────────────────────
    combined_df = combined_df.drop_duplicates(subset=['Date'], keep='last')
    combined_df = combined_df.sort_values(by='Date').reset_index(drop=True)
    combined_df.to_parquet(silver_path, index=False, engine='pyarrow')

    print(f"[{ticker}] Silver updated. Total rows: {len(combined_df)}")