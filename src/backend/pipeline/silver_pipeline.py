import os
import pandas as pd
from backend.utils import calculate_lookback_date
from backend.data_processor.indicators import apply_indicators
from backend.data_processor.sentiment import compute_sentiment_feature

def update_silver_pipeline(ticker, interval="daily", lookback_days=60):
    """
    Reads bronze data, calculates indicators safely handling the lookback period, 
    and upserts into the silver data lake.
    """
    bronze_path = f"../../data/bronze/{ticker}/{interval}/data.parquet"
    silver_dir = f"../../data/silver/{ticker}/{interval}"
    silver_path = f"{silver_dir}/data.parquet"

    os.makedirs(silver_dir, exist_ok=True)

    # Make sure we have the bronze data
    if not os.path.exists(bronze_path):
        print(f"[{ticker}] Raw data not found at {bronze_path}. Please run Tier 1 first.")
        return
    
    raw_df = pd.read_parquet(bronze_path, engine='pyarrow')
    raw_df['Date'] = pd.to_datetime(raw_df['Date'])

    # Figure out the required data chunk
    if os.path.exists(silver_path):
        features_df = pd.read_parquet(silver_path, engine='pyarrow')
        features_df['Date'] = pd.to_datetime(features_df['Date'])
        
        # Grab the date of the last calculated feature
        last_feature_date = features_df['Date'].iloc[-1]
        
        # Calculate the exact calendar date we need to prime the math, 
        # accounting for crypto 24/7 vs equity holidays
        prime_date, asset_class = calculate_lookback_date(ticker, last_feature_date, lookback_days)
        
        print(f"[{ticker}] ({asset_class}) Updating features. Priming data from {prime_date.strftime('%Y-%m-%d')}...")
        
        # Slice the raw data from our calculated prime date forward
        processing_df = raw_df[raw_df['Date'] >= prime_date].copy()
        is_incremental = True
        
    else:
        # First time calculating features
        processing_df = raw_df.copy()
        features_df = pd.DataFrame() 
        print(f"[{ticker}] No existing features. Calculating full history...")
        is_incremental = False

    # Compute indicators
    processing_df = apply_indicators(processing_df)

    # Compute and merge the AI Sentiment Feature
    sentiment_df = compute_sentiment_feature(ticker, interval)

    # Merge the sentiment column into your main OHLCV+Indicators dataframe
    processing_df = processing_df.join(sentiment_df, how='left')
    processing_df['Sentiment'] = processing_df['Sentiment'].ffill().fillna(0.0)

    # Clean up and Upsert
    if is_incremental:
        # If the new columns don't match the old columns exactly...
        if set(processing_df.columns) != set(features_df.columns):
            print(f"[{ticker}] Schema change detected! Backfilling historical data...")
            
            # Re-run the math on the ENTIRE raw dataset to fill in the new columns
            processing_df = apply_indicators(raw_df.copy())
            
            # Switch off incremental mode so it overwrites the master file
            is_incremental = False

        # Keep ONLY the genuinely new rows (drop the priming rows)
        new_features = processing_df[processing_df['Date'] > last_feature_date]
        combined_df = pd.concat([features_df, new_features])
    else:
        # Drop the NaN rows created by the initial lookback window
        combined_df = processing_df.dropna(subset=['RSI'])

    # Deduplicate and sort using the 'Date' column
    combined_df = combined_df.drop_duplicates(subset=['Date'], keep='last')
    combined_df = combined_df.sort_values(by='Date')
    
    # Save with index=False
    combined_df.to_parquet(silver_path, index=False, engine='pyarrow')
    
    print(f"[{ticker}] Features updated safely. Total rows: {len(combined_df)}")