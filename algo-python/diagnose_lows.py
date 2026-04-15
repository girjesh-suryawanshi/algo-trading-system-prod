
import os
import requests
from datetime import datetime, timedelta
import json

# Setup environment (simulate strategy environment)
ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "your_token")
CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "your_id")
BASE_URL = "https://api.dhan.co"

def get_headers():
    return {
        "access-token": ACCESS_TOKEN,
        "client-id": CLIENT_ID,
        "Content-Type": "application/json"
    }

def fetch_data(security_id, interval, days=30):
    url = f"{BASE_URL}/charts/historical"
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    payload = {
        "securityId": str(security_id),
        "exchangeSegment": "NSE_FNO",
        "instrument": "OPTIDX",
        "interval": interval,
        "fromDate": from_date,
        "toDate": to_date
    }
    
    print(f"--- Fetching {interval} for ID: {security_id} ({days} days) ---")
    res = requests.post(url, json=payload, headers=get_headers())
    if res.status_code == 200:
        data = res.json()
        # Handle different response formats
        charts = data.get("data") if "open" not in data else data
        return charts
    else:
        print(f"Error {res.status_code}: {res.text}")
        return None

def diagnose():
    # Targets reported by user
    # NIFTY 25100 CE (Apr 21) - ID: 63484 (from previous logs)
    # NIFTY 22850 PE (Apr 21) - ID: 63369 (from previous logs)
    targets = [
        {"name": "NIFTY 25100 CE", "id": "63484"},
        {"name": "NIFTY 22850 PE", "id": "63369"}
    ]
    
    for t in targets:
        print(f"\n=== DIAGNOSIS FOR {t['name']} (ID: {t['id']}) ===")
        
        # 1. Daily Data
        daily = fetch_data(t['id'], "D", days=100) # Contract life (approx)
        if daily and "low" in daily:
            all_lows = daily['low']
            abs_low = min(all_lows)
            print(f"Daily API Absolute Low: {abs_low}")
            # Find April 13th
            # Timestamps are typically daily
            for i, ts in enumerate(daily.get('timestamp', [])):
                dt = datetime.fromtimestamp(ts)
                if dt.strftime("%Y-%m-%d") == "2026-04-13":
                    print(f"Daily Low on 2026-04-13: {daily['low'][i]}")
        
        # 2. Minute Data
        minute = fetch_data(t['id'], "1", days=30)
        if minute and "low" in minute:
            all_lows = [l for l in minute['low'] if l > 0]
            if all_lows:
                abs_low = min(all_lows)
                print(f"Minute API Absolute Low (Last 30 days): {abs_low}")
                # Search for any value close to user reported values (4.80 or 9.10)
                if abs_low <= 9.2:
                    print(f"SUCCESS: Found a low near user report in 1-min data!")

if __name__ == "__main__":
    diagnose()
