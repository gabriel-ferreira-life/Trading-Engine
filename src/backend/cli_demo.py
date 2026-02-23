import sys
import pandas as pd

# Import your modules
from data_raw import update_raw_pipeline
from data_features import update_features_pipeline
from engine_backtest import run_backtest
from data_eraser import erase_data 
from utils import plot_equity_curve, plot_signals, plot_montage

def run_trading_engine(ticker, strategy_name="baseline", interval="daily", start_date=None, end_date=None):
    """Executes the Medallion pipeline for a single asset."""
    print(f"\n" + "="*50)
    print(f"INITIATING ENGINE FOR: {ticker.upper()}")
    print("="*50)
    
    try:
        print("\n--- STEP 1: RAW DATA ---")
        update_raw_pipeline(ticker, interval=interval)
        
        print("\n--- STEP 2: FEATURES ---")
        update_features_pipeline(ticker, interval=interval) 
        
        print("\n--- STEP 3: BACKTEST (BASELINE) ---")
        result_df = run_backtest(ticker, strategy_name=strategy_name, interval=interval, start_date=start_date, end_date=end_date)
        
        if result_df is not None and not result_df.empty:
            # plot_equity_curve(result_df, ticker)
            # plot_signals(result_df, ticker)
            plot_montage(result_df, ticker)
            print(f"\nPIPELINE COMPLETE FOR {ticker.upper()}\n")
        else:
            print(f"\n[!] Backtest failed to generate results for {ticker.upper()}.\n")
            
    except Exception as e:
        print(f"\n[ERROR] Pipeline crashed for {ticker}: {e}\n")

def interactive_demo():
    """The interactive terminal menu for live demos."""
    print("\n" + "*"*50)
    print("   QUANTITATIVE TRADING ENGINE - LIVE DEMO   ")
    print("*"*50)
    
    while True:
        print("\nOptions:")
        print("  [1] Run Backtest on a Ticker")
        print("  [2] Clear Data Cache (Nuke & Pave)")
        print("  [3] Exit Engine")
        
        choice = input("\nSelect an option (1-3): ").strip()
        
        if choice == '1':
            ticker = input("Enter a ticker symbol (e.g., NVDA, BTC, SPY): ").strip().upper()
            strategy = input("Enter strategy name (default 'baseline'): ").strip().lower() or "baseline"
            print("\n[Optional] Define a specific time window for the backtest.")
            start_date = input("  Start Date (YYYY-MM-DD) [Default: 2020-01-01]: ").strip() or None
            end_date = input("  End Date   (YYYY-MM-DD) [Default: Today]:      ").strip() or None
            if ticker:
                run_trading_engine(ticker, strategy_name=strategy, start_date=start_date, end_date=end_date)
            else:
                print("Ticker cannot be blank.")
                
        elif choice == '2':
            # Integrated with your upgraded eraser utility
            print("\n--- DATA ERASER UTILITY ---")
            ticker = input("Enter the ticker to erase: ").strip().upper()
            stage = input("Enter stage ('raw', 'features', 'insights', 'both', 'all') [default: 'all']: ").strip().lower() or "all"
            if ticker:
                erase_data(ticker, stage=stage)
                print(f"Cache cleared for {ticker}. Next run will be a full historical fetch.")
                
        elif choice == '3' or choice.lower() in ['q', 'quit', 'exit']:
            print("\nShutting down engine. Goodbye!\n")
            sys.exit()
            
        else:
            print("\nInvalid choice. Please enter 1, 2, or 3.")

# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    interactive_demo()