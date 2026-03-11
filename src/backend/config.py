import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

# Secrets (From .env)
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_ENDPOINT")
OPENAI_KEY = os.getenv("OPENAI_KEY")

# Logic Settings (Non-Secrets)
TICKERS = ["NVDA", "AAPL", "BTC/USD"]