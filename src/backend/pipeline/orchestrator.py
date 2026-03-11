from bronze_pipeline import update_bronze_pipeline
from silver_pipeline import update_silver_pipeline
from backend.engine_backtest import run_backtest

# ==========================================
# ORCHASTRATOR
# ==========================================

def run_full_pipeline(ticker, strategy_name, interval, start_date, end_date):
    print("\n--- STEP 1: BRONZE DATA ---")
    update_bronze_pipeline(ticker, interval)

    print("\n--- STEP 2: SILVER DATA ---")
    update_silver_pipeline(ticker, interval)

    print(f"\n--- STEP 3: BACKTEST ({strategy_name}) ---")
    return run_backtest(ticker, strategy_name, interval, start_date, end_date)