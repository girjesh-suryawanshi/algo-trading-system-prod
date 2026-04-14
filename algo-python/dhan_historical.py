import os
import aiohttp
import asyncio
import pandas as pd
from datetime import datetime, timedelta

API_URL = "https://api.dhan.co/v2/charts/rollingoption"

async def fetch_strike_data_with_retry(session, strike_relative, opt_type, from_date, to_date, access_token, client_id, security_id="13", segment="NSE_FNO", expiry_flag="WEEK", expiry_code=1, interval="1", retries=1):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'access-token': access_token,
        'client-id': client_id
    }
    
    payload = {
        "exchangeSegment": segment,
        "interval": interval,
        "securityId": str(security_id),
        "instrument": "OPTIDX",
        "expiryFlag": expiry_flag,
        "expiryCode": expiry_code,
        "strike": strike_relative,
        "drvOptionType": opt_type,
        "requiredData": ["open", "high", "low", "close", "strike", "timestamp"],
        "fromDate": from_date,
        "toDate": to_date
    }
    
    for attempt in range(retries + 1):
        try:
            async with session.post(API_URL, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data, opt_type
                elif response.status == 429:
                    wait_time = 5 * (attempt + 1)
                    print(f"Rate limited (429) on {strike_relative} {opt_type}. Waiting {wait_time}s (Attempt {attempt+1}/{retries+1})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    resp_text = await response.text()
                    print(f"Dhan API Failed ({strike_relative} {opt_type}): HTTP {response.status} - {resp_text}")
                    return None, opt_type
        except Exception as e:
            print(f"Exception fetching {strike_relative} {opt_type}: {e}")
            return None, opt_type
    return None, opt_type

async def fetch_historical_chain(from_date: str, to_date: str, access_token: str, client_id: str, symbol="NIFTY", security_id="13", segment="NSE_FNO", expiry_flag="WEEK", expiry_code=1) -> pd.DataFrame:
    strikes = ["ATM"] + [f"ATM+{i}" for i in range(1, 11)] + [f"ATM-{i}" for i in range(1, 11)]
    rows = []
    
    # Calculate pre-history start (15 days before backtest)
    backtest_start = datetime.strptime(from_date, "%Y-%m-%d")
    pre_history_start = (backtest_start - timedelta(days=15)).strftime("%Y-%m-%d")
    pre_history_end = (backtest_start - timedelta(days=1)).strftime("%Y-%m-%d")

    # Use a semaphore to limit concurrency and avoid 429 errors (Rate limits)
    limit = asyncio.Semaphore(5)

    async def fetch_with_limit(session, strike, opt_type, start, end, interval):
        async with limit:
            res, o_type = await fetch_strike_data_with_retry(
                session, strike, opt_type, start, end, access_token, client_id, security_id, segment, expiry_flag, expiry_code, interval
            )
            return res, o_type, strike

    async with aiohttp.ClientSession() as session:
        # Phase 1: Pre-fetching Daily Floors
        print(f">>> [BACKTEST] Phase 1: Concurrent Pre-fetch (Floors)...")
        floor_tasks = []
        for strike in strikes:
            for opt_type in ["CALL", "PUT"]:
                floor_tasks.append(fetch_with_limit(session, strike, opt_type, pre_history_start, pre_history_end, "D"))
        
        floor_results = await asyncio.gather(*floor_tasks)
        strike_floors = {}
        for history_res, opt_type, strike in floor_results:
            floor = 999999.0
            if history_res and 'data' in history_res:
                key = 'ce' if opt_type == 'CALL' else 'pe'
                if history_res['data'].get(key) and history_res['data'][key].get('low'):
                    lows = [l for l in history_res['data'][key]['low'] if l > 0]
                    if lows: floor = min(lows)
            strike_floors[f"{strike}_{opt_type}"] = floor

        # Phase 2: Fetching 1-Minute Intraday Data
        print(f">>> [BACKTEST] Phase 2: Concurrent Intraday Fetch...")
        data_tasks = []
        for strike in strikes:
            for opt_type in ["CALL", "PUT"]:
                data_tasks.append(fetch_with_limit(session, strike, opt_type, from_date, to_date, "1"))
        
        data_results = await asyncio.gather(*data_tasks)
        
        for res, opt_type, rel_strike in data_results:
            if not res or 'data' not in res:
                continue
                
            key = 'ce' if opt_type == 'CALL' else 'pe'
            if res['data'] and key in res['data'] and res['data'][key]:
                chain_data = res['data'][key]
                if not chain_data.get('timestamp') or not chain_data.get('open'):
                    continue
                
                historical_floor = strike_floors.get(f"{rel_strike}_{opt_type}", 999999.0)
                num_records = len(chain_data['timestamp'])
                
                try:
                    for i in range(num_records):
                        stk_val = chain_data['strike'][i] if chain_data.get('strike') and len(chain_data['strike']) > i else 0
                        rows.append({
                            "timestamp": datetime.fromtimestamp(chain_data['timestamp'][i]).isoformat(),
                            "strike": int(stk_val),
                            "optionType": "CE" if opt_type == "CALL" else "PE",
                            "open": float(chain_data['open'][i]),
                            "high": float(chain_data['high'][i]),
                            "low": float(chain_data['low'][i]),
                            "close": float(chain_data['close'][i]),
                            "historical_floor": historical_floor
                        })
                except Exception: pass
                    
    return pd.DataFrame(rows)
