import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from strategy import StrategyManager
from backtest_engine import run_backtest
from dhan_historical import fetch_historical_chain
from pydantic import BaseModel
import pandas as pd
from typing import Dict

app = FastAPI(title="LuminaQuant Strategy Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Multi-User Management
user_managers: Dict[int, StrategyManager] = {}
user_tasks: Dict[int, asyncio.Task] = {}

async def run_user_loop(user_id: int):
    print(f">>> [ENGINE] Starting loop for User {user_id}")
    while user_id in user_managers:
        try:
            manager = user_managers[user_id]
            await asyncio.to_thread(manager.run_strategy)
        except Exception as e:
            print(f">>> [ENGINE] Strategy error for User {user_id}: {e}")
        await asyncio.sleep(5)
    print(f">>> [ENGINE] Stopped loop for User {user_id}")

class EngineRequest(BaseModel):
    userId: int
    accessToken: str
    clientId: str
    targetPriceLimit: float = 12.0

@app.post("/engine/start")
async def start_engine(req: EngineRequest):
    if req.userId in user_tasks:
        return {"message": f"Engine already running for User {req.userId}"}
    
    manager = StrategyManager(req.userId, req.accessToken, req.clientId, req.targetPriceLimit)
    user_managers[req.userId] = manager
    task = asyncio.create_task(run_user_loop(req.userId))
    user_tasks[req.userId] = task
    
    return {"message": f"Engine started for User {req.userId}"}

@app.post("/engine/stop")
async def stop_engine(req: EngineRequest):
    user_id = req.userId
    if user_id in user_managers:
        del user_managers[user_id]
    if user_id in user_tasks:
        user_tasks[user_id].cancel()
        del user_tasks[user_id]
    return {"message": f"Engine stopped for User {user_id}"}

@app.get("/engine/status/{user_id}")
async def get_engine_status(user_id: int):
    is_running = user_id in user_tasks
    state = user_managers[user_id].state if is_running else {}
    return {
        "auto_running": is_running,
        "strategy_state": state
    }

# --- Backtest API ---
class BacktestRequest(BaseModel):
    fromDate: str
    toDate: str
    accessToken: str
    clientId: str

@app.post("/backtest")
async def backtest(req: BacktestRequest):
    df = await fetch_historical_chain(req.fromDate, req.toDate, req.accessToken, req.clientId)
    if df.empty:
        return {"error": "No data found. Check your Dhan API keys."}
    return run_backtest(df)
