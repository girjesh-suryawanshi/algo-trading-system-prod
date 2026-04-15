import os
import json
from dhan_api import get_security_quote, get_historical_data
from datetime import datetime, timedelta

# Mock credentials
ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "your_token")
CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "your_id")

def test_v3_accuracy(security_id, name):
    print(f"\n--- VERIFYING V3 SNIPER FOR {name} (ID: {security_id}) ---")
    
    # 1. Market Snapshot (The Wick King)
    quote = get_security_quote(ACCESS_TOKEN, CLIENT_ID, security_id)
    print(f"Market Snapshot Low: {quote['low']}")
    
    # 2. Daily Scan Baseline
    daily = get_historical_data(ACCESS_TOKEN, CLIENT_ID, security_id, "NSE_FNO", days=10, interval="D")
    if daily and "data" in daily:
        daily_min = min([c['low'] for c in daily['data'] if c['low'] > 0])
        print(f"Daily Historical Min: {daily_min}")
    
    # 3. High-Res Minute Scan (45 Days deeper)
    # We'll just check the most recent 3-day chunk to see if it's responsive
    to_d = datetime.now().strftime("%Y-%m-%d")
    from_d = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    prec = get_historical_data(ACCESS_TOKEN, CLIENT_ID, security_id, "NSE_FNO", interval="1", from_date_str=from_d, to_date_str=to_d)
    if prec and "data" in prec:
        prec_min = min([c['low'] for c in prec['data'] if c['low'] > 0])
        print(f"High-Res Minute Min (3-Day): {prec_min}")

if __name__ == "__main__":
    # Test IDs provided by user
    # NIFTY 22900 PE (Apr 21)
    # NIFTY 25050 CE (Apr 21)
    test_v3_accuracy("63373", "22900 PE") # ID from previous session
    test_v3_accuracy("63372", "25050 CE") # ID from previous session
