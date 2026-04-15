import os
import requests
import json
from datetime import datetime, timedelta

def get_headers():
    return {
        "access-token": os.environ.get("DHAN_ACCESS_TOKEN"),
        "client-id": os.environ.get("DHAN_CLIENT_ID"),
        "Content-Type": "application/json"
    }

def compare_historical_vs_rolling(security_id, from_date, to_date):
    print(f"\n--- DIAGNOSING SECURITY ID: {security_id} ---")
    
    # 1. Standard Historical
    hist_url = "https://api.dhan.co/v2/charts/historical"
    payload_hist = {
        "securityId": str(security_id),
        "exchangeSegment": "NSE_FNO",
        "instrument": "OPTIDX",
        "interval": "D",
        "fromDate": from_date,
        "toDate": to_date
    }
    
    res_hist = requests.post(hist_url, json=payload_hist, headers=get_headers())
    print(f"Historical result (D): {res_hist.status_code}")
    hist_data = res_hist.json().get('data', {})
    if 'low' in hist_data:
        print(f"Historical Daily Lows: {hist_data['low']}")
        print(f"Historical Min: {min(hist_data['low'])}")
    else:
        print("No historical low data found.")

    # 2. Rolling Option (The one we use in backtests)
    roll_url = "https://api.dhan.co/v2/charts/rollingoption"
    payload_roll = {
        "exchangeSegment": "NSE_FNO",
        "interval": "D",
        "securityId": "13", # NIFTY underlying for index options
        "instrument": "OPTIDX",
        "expiryFlag": "WEEK",
        "expiryCode": 1,
        "strike": "ATM", # This is tricky for diagnostic without knowing the exact strike relative
        "drvOptionType": "CALL",
        "requiredData": ["low"],
        "fromDate": from_date,
        "toDate": to_date
    }
    # Note: Rolling API requires strike relative. For diagnostics we might need the specific option security ID
    # But since the user gave specific security IDs (based on UI), /charts/historical is the one that uses them.

    # 3. Standard Historical 1-Min (Stage 2 in App)
    payload_hist_1m = payload_hist.copy()
    payload_hist_1m["interval"] = "1"
    res_hist_1m = requests.post(hist_url, json=payload_hist_1m, headers=get_headers())
    print(f"Historical result (1m): {res_hist_1m.status_code}")
    hist_1m_data = res_hist_1m.json().get('data', {})
    if 'low' in hist_1m_data:
        print(f"Historical 1m Min: {min(hist_1m_data['low'])}")
    else:
        print("No 1m historical low data found.")

if __name__ == "__main__":
    # User's reported instruments (Need to find their IDs first but we can test with the Logic)
    # Today is April 15. April 13 is target.
    from_dt = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    to_dt = datetime.now().strftime("%Y-%m-%d")
    
    # Example test cases (IDs are usually 5 digits)
    # The user mentioned 25100 CE and 22850 PE.
    print(f"Range: {from_dt} to {to_dt}")
    # compare_historical_vs_rolling("ID_HERE", from_dt, to_dt)
