import os
import json
from dhan_api import get_historical_data
from datetime import datetime

def find_wick_on_day(security_id, timestamp):
    day_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
    print(f"\n--- SCANNING MINUTE DATA FOR {day_str} (ID: {security_id}) ---")
    
    access_token = os.getenv("DHAN_ACCESS_TOKEN")
    client_id = os.getenv("DHAN_CLIENT_ID")
    
    # Fetch 1-minute for this specific day
    data = get_historical_data(
        access_token, client_id, security_id, "NSE_FNO",
        interval="1", from_date_str=day_str, to_date_str=day_str
    )
    
    if data and "data" in data:
        lows = [c['low'] for c in data['data'] if c['low'] > 0]
        if lows:
            print(f"Minute Lows found: {min(lows)} to {max(lows)}")
            print(f"Absolute Min on this day: {min(lows)}")
        else:
            print("No minute data for this day.")
    else:
        print(f"API Error/No data: {data}")

if __name__ == "__main__":
    # From user's log for 63482, timestamp 1775413800 had low 8.1
    find_wick_on_day("63482", 1775413800)
    # From user's log for 63373, timestamp 1775759400 had low 36.75 (wait, user says 10.30)
    # Actually, let's just scan the last 90 days in 1-day chunks.
