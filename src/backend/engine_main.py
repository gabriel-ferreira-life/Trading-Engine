from tier1_raw import update_raw_pipeline
from tier2_features import update_features_pipeline

if __name__ == "__main__":
    # Example usage: Update raw data for NVDA
    update_raw_pipeline("BTC", interval="daily", default_start="2025-12-01")

    # Compute indicators for NVDA
    update_features_pipeline("BTC", interval="daily", lookback_days=22)