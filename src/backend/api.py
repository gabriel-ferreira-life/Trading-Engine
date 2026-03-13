import os
import json
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.pipeline.orchestrator import run_full_pipeline, run_comparison_pipeline
from backend.trading_strategy.registry import STRATEGIES

app = FastAPI(title="Trading Engine API", version="1.0")

# ==========================================
# REQUEST MODELS (What the UI sends)
# ==========================================
class BacktestRequest(BaseModel):
    ticker:     str
    strategy:   str = "baseline"
    interval:   str = "daily"
    start_date: Optional[str] = None
    end_date:   Optional[str] = None

class CompareRequest(BaseModel):
    ticker:     str
    interval:   str = "daily"
    start_date: Optional[str] = None
    end_date:   Optional[str] = None

# ==========================================
# SINGLE STRATEGY (What the API does)
# ==========================================
@app.post("/api/v1/backtest")
def trigger_backtest(request: BacktestRequest):
    ticker = request.ticker.upper()

    try:
        # Update the data lake and Execute backtest
        result_df = run_full_pipeline(
            ticker        = ticker,
            strategy_name = request.strategy,
            interval      = request.interval,
            start_date    = request.start_date,
            end_date      = request.end_date
        )

        if result_df is None or result_df.empty:
            raise HTTPException(status_code=400, detail=f"Backtest returned no data for {ticker}.")
        
        # Read JSON metrics we just created
        metrics_path = f"../../data/gold/{ticker}/{request.interval}/{request.strategy}/{request.strategy}_metrics.json"

        if not os.path.exists(metrics_path):
             raise HTTPException(status_code=500, detail="Engine succeeded, but metrics JSON was not found on disk.")
        
        with open(metrics_path, "r") as f:
            summary_metrics = json.load(f)

        return {
            "status": "success",
            "message": f"Backtest pipeline completed successfully for {ticker}.",
            "data_files": {
                "dataset": f"../../data/gold/{ticker}/{request.interval}/{request.strategy}/{request.strategy}_dataset.parquet",
                "trades": f"../../data/gold/{ticker}/{request.interval}/{request.strategy}/{request.strategy}_trades.parquet",
                "metrics_json": f"../../data/gold/{ticker}/{request.interval}/{request.strategy}/{request.strategy}_metrics.json"
            },
            "summary": summary_metrics  # The UI will use this to build the scorecard!
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ==========================================
# ALL STRATEGIES  —  /api/v1/compare
# ==========================================
 
@app.post("/api/v1/compare")
def trigger_comparison(request: CompareRequest):
    """
    Runs the full pipeline once (bronze + silver), then backtests every
    registered strategy. Returns per-strategy metrics and file paths.
    """
    ticker = request.ticker.upper()
    try:
        _, summaries = run_comparison_pipeline(
            ticker     = ticker,
            interval   = request.interval,
            start_date = request.start_date,
            end_date   = request.end_date,
        )
 
        if not summaries:
            raise HTTPException(status_code=400, detail=f"No strategies produced results for {ticker}.")
 
        # Build file path map and load each metrics JSON
        strategies_out = {}
        for strategy_name in summaries:
            gold_dir = f"../../data/gold/{ticker}/{request.interval}/{strategy_name}"
            strategies_out[strategy_name] = {
                "summary": summaries[strategy_name],
                "data_files": {
                    "dataset": f"{gold_dir}/{strategy_name}_dataset.parquet",
                    "trades":  f"{gold_dir}/{strategy_name}_trades.parquet",
                    "metrics": f"{gold_dir}/{strategy_name}_metrics.json",
                },
            }
 
        return {
            "status":     "success",
            "ticker":     ticker,
            "strategies": strategies_out,            # keyed by strategy name
            "available":  list(STRATEGIES.keys()),   # lets the UI know what exists
        }
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    print("🚀 Starting Trading Engine API on http://0.0.0.0:8000")
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)