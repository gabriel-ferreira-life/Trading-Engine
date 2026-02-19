import os

def erase_data(ticker, interval="daily", stage="all"):
    """
    Quickly deletes the parquet files for a given ticker and interval.
    
    Parameters:
    ticker (str): The asset ticker (e.g., 'NVDA', 'BTC-USD').
    interval (str): The timeframe (default: 'daily').
    stage (str): Which tier to delete - 'raw', 'features', 'insights', 'both' (raw+features), or 'all'.
    """
    # Route the logic based on the requested stage
    stages_to_delete = []
    stage_lower = stage.lower()
    
    if stage_lower == "all":
        stages_to_delete = ["raw", "features", "insights"]
    elif stage_lower == "both":
        stages_to_delete = ["raw", "features"]
    elif stage_lower in ["raw", "features", "insights"]:
        stages_to_delete = [stage_lower]
    else:
        print(f"Error: Invalid stage '{stage}'. Choose 'raw', 'features', 'insights', 'both', or 'all'.")
        return

    # Execute the deletion
    for s in stages_to_delete:
        stage_dir = f"../../data/{s}/{ticker}/{interval}"
        
        # INSIGHTS TIER: Delete all varying parquet files (e.g., baseline_results.parquet)
        if s == "insights":
            if os.path.exists(stage_dir):
                files_deleted = 0
                for file in os.listdir(stage_dir):
                    if file.endswith(".parquet"):
                        try:
                            os.remove(os.path.join(stage_dir, file))
                            print(f"[SUCCESS] Erased {file} in INSIGHTS for {ticker}.")
                            files_deleted += 1
                        except Exception as e:
                            print(f"[ERROR] Could not delete {file}: {e}")
                if files_deleted == 0:
                    print(f"[SKIP] No .parquet files found to delete in INSIGHTS for {ticker}.")
            else:
                print(f"[SKIP] No INSIGHTS directory found for {ticker} at: {stage_dir}")
                
        # RAW & FEATURES TIERS: Delete the master data.parquet file
        else:
            file_path = f"{stage_dir}/data.parquet"
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
    print("--- DATA ERASER UTILITY ---")
    ticker = input("Enter the ticker symbol (e.g., 'NVDA', 'BTC'): ").strip().upper()
    interval = input("Enter the interval (default: 'daily'): ").strip() or "daily"
    stage = input("Enter the stage to erase ('raw', 'features', 'insights', 'both', 'all') [default: 'all']: ").strip().lower() or "all"
    
    print("\nExecuting deletion...")
    erase_data(ticker, interval=interval, stage=stage)
    print("Done.\n")