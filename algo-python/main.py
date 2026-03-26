from fastapi import FastAPI, BackgroundTasks
from strategy import run_strategy, state
from backtest_engine import run_backtest
import pandas as pd

app = FastAPI(title="Algo Strategy Engine")

@app.get("/run")
def run():
    return run_strategy()

@app.get("/status")
def status():
    return state

@app.post("/backtest")
def backtest():
    # In real scenario, would load from DB/CSV
    # Mock data for demonstration
    mock_data = pd.DataFrame([
        {"strike": 23500, "low": 4.5, "high": 12.0, "close": 11.0},
        {"strike": 23500, "low": 4.0, "high": 8.5, "close": 8.0},
    ])
    return run_backtest(mock_data)
