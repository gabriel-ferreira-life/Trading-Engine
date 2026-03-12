import os
import pandas as pd
from datetime import timedelta


DEFAULT_START = "2019-01-01"


def get_fetch_range(data_path: str, date_col: str, default_start: str = DEFAULT_START) -> tuple[str | None, bool]:
    """
    Inspects an existing parquet file and returns the date range needed to
    bring it up to date. Works for any time series data source.

    Returns:
        (fetch_start, is_up_to_date)
        - fetch_start:    The date string to start fetching from, or default_start if no file exists.
        - is_up_to_date:  True if no fetch is needed (already current).
    """
    if os.path.exists(data_path):
        existing_df = pd.read_parquet(data_path, engine='pyarrow')

        if existing_df.empty:
            return default_start, False

        last_date = pd.to_datetime(existing_df[date_col].iloc[-1])
        fetch_start = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")

        if pd.to_datetime(fetch_start) > pd.Timestamp.today():
            return fetch_start, True  # Already fully up to date

        return fetch_start, False

    return default_start, False


def upsert_parquet(new_df: pd.DataFrame, data_path: str, date_col: str) -> int:
    """
    Upserts new_df into an existing parquet file, deduplicating on date_col.
    Creates the file if it doesn't exist. Works for any time series data source.

    Returns:
        Total row count of the saved file.
    """
    os.makedirs(os.path.dirname(data_path), exist_ok=True)

    if os.path.exists(data_path):
        existing_df = pd.read_parquet(data_path, engine='pyarrow')
        combined_df = pd.concat([existing_df, new_df])
    else:
        combined_df = new_df.copy()

    combined_df[date_col] = pd.to_datetime(combined_df[date_col])
    combined_df = combined_df.drop_duplicates(subset=[date_col], keep='last')
    combined_df = combined_df.sort_values(by=date_col).reset_index(drop=True)
    combined_df.to_parquet(data_path, index=False, engine='pyarrow')

    return len(combined_df)