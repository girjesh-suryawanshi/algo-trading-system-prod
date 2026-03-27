import asyncio
from fastapi import FastAPI, BackgroundTasks
from strategy import run_strategy, state
from backtest_engine import run_backtest
import pandas as pd

app = FastAPI(title="Algo Strategy Engine")

is_auto_running = False

@app.get("/start")
def start_auto():
    global is_auto_running
    is_auto_running = True
    return {"message": "Auto-trading started. Scanning market every 5 seconds..."}

@app.get("/stop")
def stop_auto():
    global is_auto_running
    is_auto_running = False
    return {"message": "Auto-trading stopped."}

async def trading_loop():
    while True:
        if is_auto_running:
            try:
                # Run the synchronous strategy function in a separate thread so it doesn't block FastAPI
                await asyncio.to_thread(run_strategy)
            except Exception as e:
                print(f"Strategy error in background loop: {e}")
        # Wait 5 seconds before the next check
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    # Start the continuous background loop when the API server starts
    asyncio.create_task(trading_loop())

@app.get("/run")
def run():
    return run_strategy()

@app.get("/status")
def status():
    return {
        "auto_running": is_auto_running,
        "strategy_state": state
    }

@app.post("/backtest")
def backtest():
    # In real scenario, would load from DB/CSV
    # Mock data for demonstration
    mock_data = pd.DataFrame([
        {"strike": 23500, "low": 4.5, "high": 12.0, "close": 11.0},
        {"strike": 23500, "low": 4.0, "high": 8.5, "close": 8.0},
    ])
    return run_backtest(mock_data)
