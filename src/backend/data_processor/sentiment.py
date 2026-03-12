import os
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from backend import config


SENTIMENT_PROMPT = PromptTemplate.from_template("""
Analyze these headlines for {ticker}.
Score the overall narrative from -1.0 (Panic/Crisis) to 1.0 (Euphoria/Growth).
Headlines:
{news}
Return ONLY the numerical score. No explanation.
""")


def compute_sentiment_feature(ticker: str, interval: str = "daily", since_date=None) -> pd.DataFrame:
    """
    Reads bronze news, scores each trading day with an LLM, and returns
    a daily sentiment DataFrame indexed by Date.

    Args:
        since_date: If provided, only scores news on dates AFTER this value.
                    Pass last_feature_date from silver pipeline for delta updates.

    Returns:
        DataFrame with index='Date' and column='Sentiment'.
        Returns an empty DataFrame (with correct shape) if no news is found.
    """
    bronze_news_path = f"../../../data/bronze/{ticker}/{interval}/news.parquet"
    empty_result = pd.DataFrame(columns=['Date', 'Sentiment']).set_index('Date')

    if not os.path.exists(bronze_news_path):
        print(f"[{ticker}] No raw news found. Sentiment will default to 0.0")
        return empty_result

    df_news = pd.read_parquet(bronze_news_path)

    if df_news.empty:
        return empty_result

    # Apply delta filter — only score dates we haven't processed yet
    if since_date is not None:
        since_date = pd.to_datetime(since_date)
        df_news = df_news[df_news['Date'] > since_date]

    if df_news.empty:
        print(f"[{ticker}] No new news to score since {since_date}.")
        return empty_result

    grouped_news = df_news.groupby('Date')
    print(f"[{ticker}] Scoring sentiment across {len(grouped_news)} trading days...")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=config.OPENAI_KEY)
    daily_scores = []

    for date, group in grouped_news:
        headlines = "\n- ".join(group['headline'].dropna().tolist())
        # Add counter log
        try:
            response = llm.invoke(SENTIMENT_PROMPT.format(ticker=ticker, news=headlines))
            score = float(response.content.strip())
        except Exception:
            score = 0.0  # Fallback to neutral on any LLM failure

        daily_scores.append({'Date': date, 'Sentiment': score})

    sentiment_df = pd.DataFrame(daily_scores).set_index('Date')
    return sentiment_df