from tier1_raw import update_raw_pipeline

if __name__ == "__main__":
    # Example usage: Update raw data for NVDA
    update_raw_pipeline("NVDA", interval="daily", default_start="2025-12-01")