import sys
import pandas as pd

# Import your modules
from data_raw import update_raw_pipeline
from data_features import update_features_pipeline
from engine_backtest import run_backtest
from data_eraser import erase_data 
from utils import plot_equity_curve, plot_signals, plot_montage

def run_trading_engine(ticker, interval="daily", lookback_days=60):
    """Executes the Medallion pipeline for a single asset."""
    print(f"\n" + "="*50)
    print(f"INITIATING ENGINE FOR: {ticker.upper()}")
    print("="*50)
    
    try:
        print("\n--- STEP 1: RAW DATA ---")
        update_raw_pipeline(ticker, interval=interval)
        
        print("\n--- STEP 2: FEATURES ---")
        update_features_pipeline(ticker, interval=interval, lookback_days=lookback_days) 
        
        print("\n--- STEP 3: BACKTEST (BASELINE) ---")
        result_df = run_backtest(ticker, interval=interval)
        
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
            if ticker:
                run_trading_engine(ticker)
            else:
                print("Ticker cannot be blank.")
                
        elif choice == '2':
            ticker = input("Enter the ticker to erase (or type 'ALL' to reset everything): ").strip().upper()
            if ticker == 'ALL':
                print("Warning: Bulk deletion not yet configured. Please enter a specific ticker.")
            elif ticker:
                erase_data(ticker, stage="all")
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