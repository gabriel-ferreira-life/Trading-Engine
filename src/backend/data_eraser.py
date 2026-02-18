import os

def erase_data(ticker, interval="daily", stage="both"):
    """
    Quickly deletes the master parquet files for a given ticker and interval.
    
    Parameters:
    ticker (str): The asset ticker (e.g., 'NVDA', 'BTC-USD').
    interval (str): The timeframe (default: 'daily').
    stage (str): Which tier to delete - 'raw', 'features', or 'both'.
    """
    # Route the logic based on the requested stage
    stages_to_delete = []
    
    if stage.lower() == "both":
        stages_to_delete = ["raw", "features"]
    elif stage.lower() in ["raw", "features"]:
        stages_to_delete = [stage.lower()]
    else:
        print(f"Error: Invalid stage '{stage}'. Choose 'raw', 'features', or 'both'.")
        return

    # Execute the deletion
    for s in stages_to_delete:
        # Target the specific master file 
        file_path = f"../../data/{s}/{ticker}/{interval}/data.parquet"
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"[SUCCESS] Erased {s.upper()} data for {ticker}.")
            except Exception as e:
                print(f"[ERROR] Could not delete {s.upper()} data for {ticker}: {e}")
        else:
            print(f"[SKIP] No {s.upper()} data found for {ticker} at: {file_path}")

# ==========================================
# HOW TO USE IT
# ==========================================
if __name__ == "__main__":
    ticker = input("Enter the ticker symbol (e.g., 'NVDA', 'BTC'): ")
    interval = input("Enter the interval (default: 'daily'): ") or "daily"
    stage = input("Enter the stage to erase ('raw', 'features', 'both'): ")
    erase_data(ticker, interval=interval, stage=stage)
    # Example 1: Nuke everything for NVDA to start completely fresh
    # erase_data("NVDA", stage="both")
    
    # Example 2: You tweaked your MACD math, so just wipe the Features tier
    # erase_data("BTC-USD", stage="features")
    pass