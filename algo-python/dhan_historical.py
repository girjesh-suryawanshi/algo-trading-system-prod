import os
import aiohttp
import asyncio
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "")
DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "")
API_URL = "https://api.dhan.co/v2/charts/rollingoption"

HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'access-token': DHAN_ACCESS_TOKEN,
    'client-id': DHAN_CLIENT_ID
}

async def fetch_strike_data_with_retry(session, strike_relative, opt_type, from_date, to_date, retries=1):
    payload = {
        "exchangeSegment": "NSE_FNO",
        "interval": "1",
        "securityId": 13, 
        "instrument": "OPTIDX",
        "expiryFlag": "WEEK",
        "expiryCode": 1,
        "strike": strike_relative,
        "drvOptionType": opt_type,
        "requiredData": ["open", "high", "low", "close", "strike"],
        "fromDate": from_date,
        "toDate": to_date
    }
    
    for attempt in range(retries + 1):
        try:
            async with session.post(API_URL, headers=HEADERS, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data, opt_type
                elif response.status == 429:
                    print(f"Rate limited (429) on {strike_relative} {opt_type}. Waiting 2s (Attempt {attempt+1}/{retries+1})")
                    await asyncio.sleep(2)
                    continue # Retry
                else:
                    resp_text = await response.text()
                    print(f"Dhan API Failed ({strike_relative} {opt_type}): HTTP {response.status} - {resp_text}")
                    return None, opt_type
        except Exception as e:
            print(f"Exception fetching {strike_relative} {opt_type}: {e}")
            return None, opt_type
    return None, opt_type

async def fetch_historical_chain(from_date: str, to_date: str) -> pd.DataFrame:
    # 21 strikes spanning from ATM-10 to ATM+10
    strikes = ["ATM"] + [f"ATM+{i}" for i in range(1, 11)] + [f"ATM-{i}" for i in range(1, 11)]
    
    rows = []
    
    async with aiohttp.ClientSession() as session:
        results = []
        
        # Sequentially fetch to avoid DH-904 rate-limiting
        total_tasks = len(strikes) * 2
        count = 0
        
        for strike in strikes:
            for opt_type in ["CALL", "PUT"]:
                count += 1
                # Log to the container stdout so we can track progress in docker logs
                print(f">>> [BACKTEST] Progress: {count}/{total_tasks} | Fetching {strike} {opt_type}...", flush=True)
                res, o_type = await fetch_strike_data_with_retry(session, strike, opt_type, from_date, to_date)
                results.append((res, o_type))
                
                # Increased 1.5s delay to safely stay under Dhan 60/min limit
                await asyncio.sleep(1.5)
            
        for res, opt_type in results:
            if not res or 'data' not in res:
                continue
                
            key = 'ce' if opt_type == 'CALL' else 'pe'
            if res['data'] and key in res['data'] and res['data'][key]:
                chain_data = res['data'][key]
                
                if not chain_data.get('timestamp') or not chain_data.get('open'):
                    continue
                
                num_records = len(chain_data['timestamp'])
                if num_records == 0: continue
                
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
                        })
                except Exception as e:
                    print(f"Error parsing data rows for {opt_type}: {e}")
                    
    df = pd.DataFrame(rows)
    return df
