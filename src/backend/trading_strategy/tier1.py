import pandas as pd
import numpy as np

def generate_signals_tier1(df):
    df = df.copy()
    
    df['SMA_20'] = df['Adj Close'].rolling(window=20).mean()
    df['Asset_Return'] = df['Adj Close'].pct_change()  
    positions = np.zeros(len(df))
    strategy_returns = np.zeros(len(df))
    
    in_position = False
    entry_price = 0.0
    
    # Use .values for much faster iteration
    close_prices = df['Adj Close'].values
    rsi_values = df['RSI'].values
    sma_values = df['SMA_20'].values
    
    for i in range(1, len(df)):
        # Skip if indicators aren't ready
        if np.isnan(rsi_values[i-1]) or np.isnan(sma_values[i-1]):
            continue
            
        current_price = close_prices[i]
        prev_price = close_prices[i-1]
        prev_rsi = rsi_values[i-1]
        prev_sma = sma_values[i-1]
        
        if not in_position:
            # We want RSI oversold, but price should be near or above SMA to show 'dip in uptrend'
            # If 35 is too strict, we'll try 40.
            if prev_rsi < 35 and current_price > (prev_sma * 0.98): 
                in_position = True
                entry_price = current_price
                positions[i] = 1
        
        elif in_position:
            # Calculate return from the entry price
            unrealized_return = (current_price - entry_price) / entry_price
            
            # EXIT 1: Profit Target (+2%)
            if unrealized_return >= 0.02:
                in_position = False
                # We exit at the target price
                exit_price = entry_price * 1.02
                strategy_returns[i] = (exit_price / prev_price) - 1
                positions[i] = 0
                
            # EXIT 2: Stop Loss (-1%)
            elif unrealized_return <= -0.01:
                in_position = False
                # We exit at the stop price
                exit_price = entry_price * 0.99
                strategy_returns[i] = (exit_price / prev_price) - 1
                positions[i] = 0
                
            else:
                # Still holding
                positions[i] = 1
                strategy_returns[i] = (current_price / prev_price) - 1

    df['Position'] = positions
    df['Strategy_Return'] = strategy_returns
    
    return df