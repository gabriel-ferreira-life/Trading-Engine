import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.pipeline.orchestrator import run_full_pipeline

app = FastAPI(title="Trading Engine API", version="1.0")

# ==========================================
# DEFINE THE PAYLOAD (What the UI sends)
# ==========================================
class BacktestRequest(BaseModel):
    ticker: str
    strategy: str = "baseline"
    interval: str = "daily"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    # add more param later like RSI

# ==========================================
# DEFINE THE ENDPOINT (What the API does)
# ==========================================
@app.post("/api/v1/backtest")
def trigger_backtest(request: BacktestRequest):
    ticker = request.ticker.upper()

    try:
        # Update the data lake and Execute backtest
        result_df = run_full_pipeline(
            ticker=ticker,
            strategy_name=request.strategy,
            interval=request.interval,
            start_date=request.start_date,
            end_date=request.end_date
        )

        if result_df is None or result_df.empty:
            raise HTTPException(status_code=400, detail=f"Backtest returned no data for {ticker}.")
        
        # Read JSON metrics we just created
        metrics_path = f"../../data/gold/{ticker}/{request.interval}/{request.strategy}_metrics.json"

        if not os.path.exists(metrics_path):
             raise HTTPException(status_code=500, detail="Engine succeeded, but metrics JSON was not found on disk.")
        
        with open(metrics_path, "r") as f:
            summary_metrics = json.load(f)

        return {
            "status": "success",
            "message": f"Backtest pipeline completed successfully for {ticker}.",
            "data_files": {
                "dataset": f"../../data/gold/{ticker}/{request.interval}/{request.strategy}_dataset.parquet",
                "trades": f"../../data/gold/{ticker}/{request.interval}/{request.strategy}_trades.parquet",
                "metrics_json": f"../../data/gold/{ticker}/{request.interval}/{request.strategy}_metrics.json"
            },
            "summary": summary_metrics  # The UI will use this to build the scorecard!
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    print("🚀 Starting Trading Engine API on http://0.0.0.0:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)