import os
import pandas as pd
from utils import calculate_lookback_date

# ==========================================
# MODULE 1: INDICATOR CALCULATIONS
# ==========================================

def calculate_rsi(df, period=22):
    """Calculates the Relative Strength Index."""
    # We use the 'Adj Close' to account for splits/dividends
    delta = df['Adj Close'].diff()
    
    # Separate gains and losses
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Calculate RS and RSI
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Assign back to DataFrame
    df['RSI'] = rsi
    return df

# ==========================================
# MODULE 2: THE TIER 2 ORCHESTRATOR
# ==========================================

def update_features_pipeline(ticker, interval="daily", lookback_days=22):
    """
    Reads raw data, calculates indicators safely handling the lookback period, 
    and upserts into the features data lake.
    """
    raw_path = f"../../data/raw/{ticker}/{interval}/data.parquet"
    features_dir = f"../../data/features/{ticker}/{interval}"
    features_path = f"{features_dir}/data.parquet"

    os.makedirs(features_dir, exist_ok=True)

    # Make sure we have the raw data
    if not os.path.exists(raw_path):
        print(f"[{ticker}] Raw data not found at {raw_path}. Please run Tier 1 first.")
        return
    
    raw_df = pd.read_parquet(raw_path, engine='pyarrow')
    raw_df['Date'] = pd.to_datetime(raw_df['Date'])

    # Figure out the required data chunk
    if os.path.exists(features_path):
        features_df = pd.read_parquet(features_path, engine='pyarrow')
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
    processing_df = calculate_rsi(processing_df, period=lookback_days) # RSI
    # more coming soon: SMA, EMA, MACD, Bollinger Bands, etc.

    # Clean up and Upsert
    if is_incremental:
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
    combined_df.to_parquet(features_path, index=False, engine='pyarrow')
    
    print(f"[{ticker}] Features updated safely. Total rows: {len(combined_df)}")