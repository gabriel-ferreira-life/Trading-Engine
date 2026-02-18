import pandas as pd
from pandas.tseries.offsets import CustomBusinessDay
from pandas.tseries.holiday import USFederalHolidayCalendar
from datetime import datetime, timedelta

def calculate_lookback_date(ticker, target_date_str, lookback_days=22):
    """
    Routes the date calculation based on asset class to ensure 
    lookback periods align with actual trading days.
    """
    target_date = pd.to_datetime(target_date_str)
    
    crypto_identifiers = ['BTC', 'ETH', 'SOL', '-USD']
    is_crypto = any(crypto in ticker.upper() for crypto in crypto_identifiers)
    
    if is_crypto:
        start_date_init = target_date - timedelta(days=lookback_days)
        asset_class = "Crypto"
    else:
        us_trading_days = CustomBusinessDay(calendar=USFederalHolidayCalendar())
        start_date_init = target_date - (lookback_days * us_trading_days)
        asset_class = "Equity"
        
    return start_date_init, asset_class