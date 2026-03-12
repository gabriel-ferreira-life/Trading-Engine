import pandas as pd

def calculate_rsi(df, period=22):
    """Calculates the Relative Strength Index."""
    # We use the 'Adj Close' to account for splits/dividends
    delta = df['Adj Close'].diff()
    
    # Separate gains and losses
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Calculate RS and RSI
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Assign back to DataFrame
    df['RSI'] = rsi
    return df

def calculate_sma(df, period=20):
    """Calculates the Simple Moving Average."""
    df[f'SMA_{period}'] = df['Adj Close'].rolling(window=period).mean()
    return df

def calculate_ema(df, period=20):
    """Calculates the Exponential Moving Average."""
    # adjust=False calculates it as a continuous series, standard for trading
    df[f'EMA_{period}'] = df['Adj Close'].ewm(span=period, adjust=False).mean()
    return df

def calculate_macd(df, fast=12, slow=26, signal=9):
    """Calculates the MACD, Signal Line, and Histogram."""
    ema_fast = df['Adj Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Adj Close'].ewm(span=slow, adjust=False).mean()
    
    df['MACD'] = ema_fast - ema_slow
    df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    return df


def apply_indicators(df):
    """A master wrapper to apply all active indicators."""
    df = calculate_rsi(df, period=22)
    df = calculate_sma(df, period=20)
    df = calculate_sma(df, period=50)
    df = calculate_ema(df, period=20)
    df = calculate_macd(df)
    return df