import os
import json
from dhan_api import get_historical_data, get_security_quote
from datetime import datetime, timedelta

def diagnose(security_id, name):
    print(f"\n--- DEEP DIAGNOSE FOR {name} (ID: {security_id}) ---")
    
    access_token = os.getenv("DHAN_ACCESS_TOKEN")
    client_id = os.getenv("DHAN_CLIENT_ID")
    
    # 1. Check Quote Session Low
    quote = get_security_quote(access_token, client_id, security_id)
    print(f"Current Session Low: {quote['low']}")
    
    # 2. Check Daily Data (150 Days)
    daily = get_historical_data(access_token, client_id, security_id, "NSE_FNO", days=150, interval="D")
    if daily and "data" in daily:
        daily_lows = [c['low'] for c in daily['data'] if c['low'] > 0]
        if daily_lows:
            print(f"Daily API Absolute Min (150d): {min(daily_lows)}")
        else:
            print("No Daily data found.")
    
    # 3. Check Minute Data (Full 150 Days Scan in chunks)
    print("Scanning 150 days of 1-minute data (this will take time)...")
    minute_lows = []
    
    # Scan last 150 days in 3-day chunks
    for i in range(50):
        to_d = (datetime.now() - timedelta(days=i*3)).strftime("%Y-%m-%d")
        from_d = (datetime.now() - timedelta(days=(i+1)*3)).strftime("%Y-%m-%d")
        
        prec = get_historical_data(
            access_token, client_id, security_id, "NSE_FNO", 
            interval="1", from_date_str=from_d, to_date_str=to_d
        )
        if prec and "data" in prec:
            chunk_lows = [c['low'] for c in prec['data'] if c['low'] > 0]
            if chunk_lows:
                minute_lows.extend(chunk_lows)
        
    if minute_lows:
        print(f"1-Minute API Absolute Min (150d): {min(minute_lows)}")
    else:
        print("No Minute data found in scan.")

if __name__ == "__main__":
    # NIFTY 22900 PE
    diagnose("63373", "22900 PE")
    # NIFTY 25050 CE
    diagnose("63482", "25050 CE")
