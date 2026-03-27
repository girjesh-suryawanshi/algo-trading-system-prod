import asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from strategy import run_strategy, state
from backtest_engine import run_backtest
from dhan_historical import fetch_historical_chain
from pydantic import BaseModel
import pandas as pd

app = FastAPI(title="Algo Strategy Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class BacktestRequest(BaseModel):
    fromDate: str
    toDate: str

@app.post("/backtest")
async def backtest(req: BacktestRequest):
    df = await fetch_historical_chain(req.fromDate, req.toDate)
    if df.empty:
        return {"error": "No historical data fetched from Dhan for this date range. Check API limits or date validity."}
    return run_backtest(df)
