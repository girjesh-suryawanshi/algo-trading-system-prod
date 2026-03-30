from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from dhan_api import get_expiry_list, get_option_chain
from strategy import StrategyManager
from backtest_engine import run_backtest
from dhan_historical import fetch_historical_chain
from pydantic import BaseModel
import pandas as pd
from typing import Dict, Any

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
    symbol: str = "NIFTY"
    securityId: str = "13"
    segment: str = "IDX_I"
    expiry: str = ""

@app.get("/instruments")
async def get_instruments():
    return {
        "data": {
            "NIFTY": {"id": 13, "segment": "IDX_I"},
            "BANKNIFTY": {"id": 25, "segment": "IDX_I"},
            "FINNIFTY": {"id": 27, "segment": "IDX_I"},
            "SENSEX": {"id": 1, "segment": "IDX_I"}
        }
    }

@app.post("/fetch-expiries")
async def fetch_expiries(req: Dict[str, Any]):
    return {
        "data": get_expiry_list(
            req.get("accessToken"), 
            req.get("clientId"), 
            req.get("securityId"), 
            req.get("segment", "IDX_I")
        )
    }

@app.post("/engine/start")
async def start_engine(req: EngineRequest):
    if req.userId in user_tasks:
        # Stop existing first to update params
        if req.userId in user_managers: del user_managers[req.userId]
        user_tasks[req.userId].cancel()
        del user_tasks[req.userId]
        await asyncio.sleep(0.5)

    manager = StrategyManager(
        req.userId, req.accessToken, req.clientId, 
        req.targetPriceLimit, req.symbol, req.securityId, 
        req.segment, req.expiry
    )
    user_managers[req.userId] = manager
    task = asyncio.create_task(run_user_loop(req.userId))
    user_tasks[req.userId] = task
    
    return {"message": f"Engine started for User {req.userId} on {req.symbol}"}

@app.post("/engine/stop")
async def stop_engine(req: Dict[str, Any]):
    user_id = req.get("userId")
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
