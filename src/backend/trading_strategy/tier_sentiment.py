import pandas as pd
import numpy as np

def generate_signals_sentiment(df, current_sentiment=0.0):
    """
    Tier Sentiment Strategy: Sentiment-Adjusted RSI
    Shifts the RSI buy/sell bands dynamically based on LLM narrative scoring.
    """
    df = df.copy()
    
    # If historical sentiment isn't in the dataframe, use the live current_sentiment
    if 'Sentiment' not in df.columns:
        df['Sentiment'] = current_sentiment

    # Initialize columns
    df['Buy_Signal'] = 0
    df['Sell_Signal'] = 0

    # ==========================================
    # REGIME 1: NEUTRAL (Standard Baseline)
    # ==========================================
    neutral_mask = (df['Sentiment'] >= -0.3) & (df['Sentiment'] <= 0.3)
    df.loc[neutral_mask & (df['RSI'] < 35), 'Buy_Signal'] = 1
    df.loc[neutral_mask & (df['RSI'] > 65), 'Sell_Signal'] = -1

    # ==========================================
    # REGIME 2: BULLISH (Buy earlier, sell later)
    # ==========================================
    bullish_mask = df['Sentiment'] > 0.3
    df.loc[bullish_mask & (df['RSI'] < 45), 'Buy_Signal'] = 1
    df.loc[bullish_mask & (df['RSI'] > 75), 'Sell_Signal'] = -1

    # ==========================================
    # REGIME 3: BEARISH (Demand extreme fear, sell early)
    # ==========================================
    bearish_mask = df['Sentiment'] < -0.3
    df.loc[bearish_mask & (df['RSI'] < 25), 'Buy_Signal'] = 1
    df.loc[bearish_mask & (df['RSI'] > 55), 'Sell_Signal'] = -1

    # ==========================================
    # POSITION SIZING & RETURNS
    # ==========================================
    df['Signal'] = df['Buy_Signal'] + df['Sell_Signal']
    
    # Forward fill the position (hold until sell signal)
    df['Position'] = df['Signal'].replace(0, np.nan).ffill().fillna(0)
    
    # Ensure we only hold Long positions (no shorting)
    df['Position'] = df['Position'].apply(lambda x: 1 if x == 1 else 0)

    # Calculate strategy returns if the engine hasn't already
    if 'Asset_Return' not in df.columns:
        df['Asset_Return'] = df['Adj Close'].pct_change()
        
    df['Strategy_Return'] = df['Asset_Return'] * df['Position']

    return df