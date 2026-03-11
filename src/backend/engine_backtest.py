import os
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from backend.trading_strategy.registry import get_strategy
from backend.utils import lake_read_parquet

def extract_trade_log(df):
    """
    Scans the vectorized backtest DataFrame, groups the 1s and 0s into 
    discrete trades, and calculates the win rate and average profit.
    """
    pos = df['Position'].fillna(0)
    changes = pos.diff()
    
    # Grab the exact dates from the Index where changes happen
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

    return pd.DataFrame(trade_ledger)

def compute_insights(df, ticker):
    """Calculates performance metrics and returns them as a dictionary, along with the trade ledger."""

    # Calculate Returns
    df['Asset_Return'] = df['Adj Close'].pct_change()
    df['Strategy_Return'] = df['Asset_Return'] * df['Position']
    
    # Calculate Equity Curves
    df['Asset_Equity'] = (1 + df['Asset_Return']).cumprod().fillna(1.0)
    df['Strategy_Equity'] = (1 + df['Strategy_Return']).cumprod().fillna(1.0)

    # CALCULATE DRAWDOWN
    df['Peak'] = df['Strategy_Equity'].cummax()
    df['Drawdown'] = (df['Strategy_Equity'] - df['Peak']) / df['Peak']
    max_dd = float(df['Drawdown'].min())

    # CALCULATE SHARPE RATIO
    daily_rets = df['Strategy_Return'].fillna(0)
    if daily_rets.std() != 0:
        sharpe = float((daily_rets.mean() / daily_rets.std()) * (252**0.5))
    else:
        sharpe = 0.0
    
    now = pd.Timestamp.now().strftime('%Y-%m-%d')
    start_date = df.index[0]
    end_date = df.index[-1]
    total_asset_return = df['Asset_Equity'].iloc[-1] - 1
    total_strategy_return = df['Strategy_Equity'].iloc[-1] - 1

    # Generate the Trade Log
    trades_df = extract_trade_log(df)

    # Calculate the Holy Grail Metrics
    if len(trades_df) > 0:

        winning_trades = trades_df[trades_df['Return'] > 0]
        losing_trades = trades_df[trades_df['Return'] <= 0]

        metrics = {
            "Simulation_Date": now,
            "Ticker": ticker,
            "Start_Date": start_date.strftime('%Y-%m-%d'),
            "End_Date": end_date.strftime('%Y-%m-%d'),
            "Total_Trading_Days": int(len(df)),
            "Total_Trades_Taken": int(len(trades_df)),
            "Buy_Hold_Return": float(total_asset_return),
            "Strategy_Return": float(total_strategy_return),
            "Performance_Delta": float(total_strategy_return - total_asset_return),
            "Win_Rate": float(len(winning_trades) / len(trades_df)),
            "Max_Drawdown": max_dd,
            "Sharpe_Ratio": sharpe,
            "Average_Win": float(winning_trades['Return'].mean()) if not winning_trades.empty else 0.0,
            "Average_Loss": float(losing_trades['Return'].mean()) if not losing_trades.empty else 0.0,
            "Best_Trade": float(trades_df['Return'].max()),
            "Worst_Trade": float(trades_df['Return'].min())
        }
        
        print(f"\n=== TRADE LOG SUMMARY ===")
        print(f"Start Date:         {metrics["Start_Date"]}")
        print(f"End Date:           {metrics["End_Date"]}")
        print(f"Total Trading Days: {len(df)}")
        print(f"Total Trades Taken: {len(trades_df)}")
        print(f"Win Rate:           {metrics["Win_Rate"]:.2%}")
        print(f"Max Drawdown:       {metrics['Max_Drawdown']:.2%}")
        print(f"Sharpe Ratio:       {metrics['Sharpe_Ratio']:.2f}")
        print(f"Average Win:        {metrics["Average_Win"]:.2%}")
        print(f"Average Loss:       {metrics["Average_Loss"]:.2%}")
        print(f"Best Trade:         {trades_df['Return'].max():.2%}")
        print(f"Worst Trade:        {trades_df['Return'].min():.2%}")
        print("=========================\n")

        print(f"=== {ticker} BASELINE BACKTEST RESULTS ===")
        print(f"Total Trading Days: {len(df)}")
        print(f"Buy & Hold Return:  {total_asset_return:.2%}")
        print(f"Strategy Return:    {total_strategy_return:.2%}")
        print(f"Performance Delta:  {(total_strategy_return - total_asset_return):.2%}")
        print("=========================================\n")    

        return metrics, df
    
    else:
        print("\n[!] No trades executed during this period.")
        return None, df

   

def run_backtest(ticker, strategy_name="baseline", interval="daily", start_date="2020-01-01", end_date=None):
    """Executes the backtest and outputs performance metrics."""

    # Setup the 3 distinct output file paths
    gold_dir = f"../../data/gold/{ticker}/{interval}"
    os.makedirs(gold_dir, exist_ok=True)

    dataset_path = f"{gold_dir}/{strategy_name}_dataset.parquet"
    trades_path = f"{gold_dir}/{strategy_name}_trades.parquet"
    metrics_path = f"{gold_dir}/{strategy_name}_metrics.json"
    
    # Data source path
    silver_path = f"../../data/silver/{ticker}/{interval}/data.parquet"

    if not os.path.exists(silver_path):
        print(f"[{ticker}] No silver data found. Run Tier 2 first.")
        return
    
    if not start_date:
        start_date = "2020-01-01"
    if not end_date:
        end_date = pd.Timestamp.now().strftime('%Y-%m-%d')

    # Read features df
    df = lake_read_parquet(silver_path, start_date=start_date, end_date=end_date)

    if len(df) > 0:
        # Get and apply the strategy function to generate signals and positions
        strategy_fn = get_strategy(strategy_name)
        df = strategy_fn(df)

        # Compute metrics
        metrics_dict, trades_df = compute_insights(df, ticker)
        
        # Save outputs
        df.reset_index().to_parquet(dataset_path, index=False, engine='pyarrow') # Timeseries

        if not trades_df.empty:
            trades_df.to_parquet(trades_path, index=False, engine='pyarrow') # Trade logs
            
        with open(metrics_path, "w") as f:
            json.dump(metrics_dict, f, indent=4) # Simulation results
    
    else:
        print("No data found to process.")
    
    return df