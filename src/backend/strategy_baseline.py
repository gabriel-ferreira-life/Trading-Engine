import pandas as pd
import numpy as np

def generate_signals(df, rsi_lower=35, rsi_upper=65):
    """
    Baseline Strategy: RSI 35/65 Mean Reversion
    - Goes Long when RSI drops below 35.
    - Closes Position (Flat) when RSI crosses above 65.
    - No risk management or stop losses.
    """
    # Create a copy to avoid altering our pristine features data
    signals_df = df.copy()
    
    # Initialize the Signal column with NaNs
    signals_df['Signal'] = np.nan
    
    # Apply the Entry and Exit Rules
    # We assign 1 for a Buy, and 0 for a Sell (Close position)
    signals_df.loc[signals_df['RSI'] < rsi_lower, 'Signal'] = 1
    signals_df.loc[signals_df['RSI'] > rsi_upper, 'Signal'] = 0
    
    # State Machine (The "Ride the full move" logic)
    # Forward-fill the signals. If we bought (1), it stays 1 until we hit a sell (0).
    # Any NaNs at the very beginning before our first signal become 0 (Flat).
    signals_df['Position'] = signals_df['Signal'].ffill().fillna(0)
    
    # PREVENTING LOOK-AHEAD BIAS
    # If RSI drops below 35 today, we cannot buy at today's close because 
    # the market is already closed by the time we calculate it. 
    # We must shift the position forward by 1 day to trade on tomorrow's action.
    signals_df['Position'] = signals_df['Position'].shift(1).fillna(0)
    
    return signals_df