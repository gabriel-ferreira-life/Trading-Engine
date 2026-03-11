import os
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from backend import config

# ==========================================
# SENTIMENT INDICATOR
# ==========================================

def compute_sentiment_feature(ticker, interval="daily"):
    """Reads raw news, queries the LLM, and returns a daily sentiment dataframe."""
    bronze_news_path = f"../../data/bronze/{ticker}/{interval}/news.parquet"
    
    if not os.path.exists(bronze_news_path):
        print(f"[SKIP] No raw news found for {ticker}. Sentiment will be 0.0")
        return pd.DataFrame(columns=['Date', 'Sentiment']).set_index('Date')
        
    df_news = pd.read_parquet(bronze_news_path)
    
    # Standardize the date so we can merge it with daily price data
    df_news['Date'] = pd.to_datetime(df_news['created_at']).dt.tz_localize(None).dt.normalize()
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_KEY)
    template = """
    Analyze these headlines for {ticker}. 
    Score the narrative from -1.0 (Panic/Crisis) to 1.0 (Euphoria/Growth).
    Headlines: {news}
    Return ONLY the numerical score.
    """
    prompt = PromptTemplate.from_template(template)
    
    daily_scores = []
    grouped_news = df_news.groupby('Date')
    
    print(f"Computing LLM Sentiment across {len(grouped_news)} trading days...")
    
    for date, group in grouped_news:
        headlines = "\n- ".join(group['headline'].dropna().tolist())
        
        try:
            response = llm.invoke(prompt.format(ticker=ticker, news=headlines))
            score = float(response.content.strip())
        except Exception:
            score = 0.0 # Fallback to neutral on LLM failure
            
        daily_scores.append({'Date': date, 'Sentiment': score})
        
    sentiment_df = pd.DataFrame(daily_scores).set_index('Date')
    return sentiment_df