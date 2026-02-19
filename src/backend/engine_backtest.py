import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from strategy_baseline import generate_signals

def extract_trade_log(df):
    """
    Scans the vectorized backtest DataFrame, groups the 1s and 0s into 
    discrete trades, and calculates the win rate and average profit.
    """
    pos = df['Position'].fillna(0)
    changes = pos.diff()
    
    # 1. Grab the exact dates from the Index where changes happen
    entries = df[changes == 1].index
    exits = df[changes == -1].index
    
    # Force-close any open positions at the end of the dataset
    if len(entries) > len(exits):
        exits = exits.append(pd.Index([df.index[-1]]))
        
    trade_ledger = []
    
    for entry_date, exit_date in zip(entries, exits):
        
        # Calculate compounded return for this specific holding period
        trade_returns = df.loc[entry_date:exit_date, 'Strategy_Return']
        trade_profit = (1 + trade_returns).prod() - 1
        
        # Calculate holding period (Calendar Days vs Trading Days)
        calendar_days = (exit_date - entry_date).days
        trading_days = df.index.get_loc(exit_date) - df.index.get_loc(entry_date)
        
        trade_ledger.append({
            'Entry_Date': entry_date,
            'Exit_Date': exit_date,
            'Trading_Days': trading_days,
            'Calendar_Days': calendar_days,
            'Return': trade_profit
        })
        
    trades_df = pd.DataFrame(trade_ledger)
    
    # 2. Calculate the Holy Grail Metrics
    if len(trades_df) > 0:
        winning_trades = trades_df[trades_df['Return'] > 0]
        losing_trades = trades_df[trades_df['Return'] <= 0]
        
        win_rate = len(winning_trades) / len(trades_df)
        avg_win = winning_trades['Return'].mean() if not winning_trades.empty else 0
        avg_loss = losing_trades['Return'].mean() if not losing_trades.empty else 0
        
        print(f"\n=== TRADE LOG SUMMARY ===")
        print(f"Total Trades Taken: {len(trades_df)}")
        print(f"Win Rate:           {win_rate:.2%}")
        print(f"Average Win:        {avg_win:.2%}")
        print(f"Average Loss:       {avg_loss:.2%}")
        print(f"Best Trade:         {trades_df['Return'].max():.2%}")
        print(f"Worst Trade:        {trades_df['Return'].min():.2%}")
        print("=========================\n")
    else:
        print("\n[!] No trades executed during this period.")
        
    return trades_df

def run_backtest(ticker, interval="daily"):
    """Executes the backtest and outputs performance metrics."""
    features_path = f"../../data/features/{ticker}/{interval}/data.parquet"
    insights_dir = f"../../data/insights/{ticker}/{interval}"
    insights_path = f"{insights_dir}/baseline_results.parquet"
    
    os.makedirs(insights_dir, exist_ok=True)

    if not os.path.exists(features_path):
        print(f"[{ticker}] No features data found. Run Tier 2 first.")
        return
    
    df = pd.read_parquet(features_path, engine='pyarrow')
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    
    # Apply Strategy
    df = generate_signals(df)
    
    # Calculate Returns
    df['Asset_Return'] = df['Adj Close'].pct_change()
    df['Strategy_Return'] = df['Asset_Return'] * df['Position']
    
    # Calculate Equity Curves
    df['Asset_Equity'] = (1 + df['Asset_Return']).cumprod().fillna(1.0)
    df['Strategy_Equity'] = (1 + df['Strategy_Return']).cumprod().fillna(1.0)
    
    # Generate the Trade Log
    trade_log_df = extract_trade_log(df)
    
    # Save the file
    df = df.reset_index()
    df.to_parquet(insights_path, index=False, engine='pyarrow')
    
    total_asset_return = df['Asset_Equity'].iloc[-1] - 1
    total_strategy_return = df['Strategy_Equity'].iloc[-1] - 1
    
    print(f"=== {ticker} BASELINE BACKTEST RESULTS ===")
    print(f"Total Trading Days: {len(df)}")
    print(f"Buy & Hold Return:  {total_asset_return:.2%}")
    print(f"Strategy Return:    {total_strategy_return:.2%}")
    print(f"Performance Delta:  {(total_strategy_return - total_asset_return):.2%}")
    print("=========================================\n")    
    return df