from .bronze_pipeline import update_bronze_pipeline
from .silver_pipeline import update_silver_pipeline
from .engine_backtest import run_backtest, run_all_strategies

def run_full_pipeline(ticker, strategy_name, interval, start_date, end_date):
    """Single-strategy pipeline. Used internally by run_comparison_pipeline."""
    print("\n--- STEP 1: BRONZE DATA ---")
    update_bronze_pipeline(ticker, interval)
 
    print("\n--- STEP 2: SILVER FEATURES ---")
    update_silver_pipeline(ticker, interval)
 
    print(f"\n--- STEP 3: BACKTEST ({strategy_name.upper()}) ---")
    return run_backtest(ticker, strategy_name, interval, start_date, end_date)
 
 
def run_comparison_pipeline(ticker, interval, start_date, end_date):
    """
    Runs bronze + silver once, then executes every registered strategy.
    Returns (results, summaries) — see run_all_strategies() for shape.
    """
    print(f"\n{'='*50}")
    print(f"  COMPARISON PIPELINE — {ticker.upper()}")
    print(f"{'='*50}")
 
    print("\n--- STEP 1: BRONZE DATA ---")
    update_bronze_pipeline(ticker, interval)
 
    print("\n--- STEP 2: SILVER FEATURES ---")
    update_silver_pipeline(ticker, interval)
 
    print("\n--- STEP 3: ALL STRATEGIES ---")
    results, summaries = run_all_strategies(
        ticker     = ticker,
        interval   = interval,
        start_date = start_date,
        end_date   = end_date,
    )
 
    print(f"\n[{ticker}] Comparison complete. Strategies run: {list(results.keys())}")
    return results, summaries