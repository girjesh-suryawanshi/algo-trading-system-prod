import requests
import json
import time
from datetime import datetime, timedelta

# DHAN CONFIG
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc2NTMwMjM0LCJpYXQiOjE3NzY0NDM4MzQsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTAxNDYzNzIzIn0.6bmb_2isZlzacZ1rtFAfr5OHFtFC1Nz-WuJTTYdwH9S7KpDF7sa1qy0qig0Ayvbpj99h6GchDPzyeXOy2XvRhw"
CLIENT_ID = "1101463723"
BASE_URL = "https://api.dhan.co/v2"

def get_headers():
    return {
        "access-token": ACCESS_TOKEN,
        "client-id": CLIENT_ID,
        "Content-Type": "application/json"
    }

def find_security_ids(symbol="NIFTY", expiry="2026-04-21"):
    print(f"\n🔍 Searching for Security IDs for {symbol} | Expiry: {expiry}")
    url = f"{BASE_URL}/optionchain"
    payload = {
        "UnderlyingScrip": 13,
        "UnderlyingSeg": "IDX_I",
        "Expiry": expiry
    }
    res = requests.post(url, json=payload, headers=get_headers())
    if res.status_code == 200:
        data = res.json().get("data", {}).get("oc", {})
        results = []
        for strike, pair in data.items():
            if strike in ["24950.0", "23500.0", "24950", "23500"]:
                for opt_type, info in pair.items():
                    results.append({
                        "strike": strike,
                        "type": opt_type.upper(),
                        "securityId": info.get("security_id"),
                        "ltp": info.get("last_price"),
                        "low": info.get("low_price")
                    })
        return results
    return []

def diagnose_security(security_id, opt_name):
    print(f"\n--- 🎯 DIAGNOSING: {opt_name} (ID: {security_id}) ---")
    
    # 1. Market Quote (Stage 0)
    res_ohlc = requests.get(f"{BASE_URL}/marketquote/ohlc/{security_id}", headers=get_headers())
    print(f"📡 Stage 0 (OHLC Quote): {res_ohlc.text}")
    
    # 2. Historical Charts (Stage 1/2)
    hist_payload = {
        "securityId": str(security_id),
        "exchangeSegment": "NSE_FNO",
        "instrument": "OPTIDX",
        "interval": "1",
        "fromDate": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "toDate": datetime.now().strftime("%Y-%m-%d")
    }
    res_hist = requests.post(f"{BASE_URL}/charts/historical", json=hist_payload, headers=get_headers())
    hist_data = res_hist.json()
    hist_lows = hist_data.get("low", [])
    if hist_lows:
        print(f"📉 Stage 1/2 (Historical Lows): Min={min(hist_lows)} | Count={len(hist_lows)}")
    else:
        print("📉 Stage 1/2 (Historical): NO DATA FOUND")

    # 3. Intraday Charts (Stage 2.5)
    intra_payload = {
        "securityId": str(security_id),
        "exchangeSegment": "NSE_FNO",
        "instrument": "OPTIDX",
        "interval": "1"
    }
    res_intra = requests.post(f"{BASE_URL}/charts/intraday", json=intra_payload, headers=get_headers())
    intra_data = res_intra.json()
    intra_lows = intra_data.get("low", [])
    if intra_lows:
        print(f"🔥 Stage 2.5 (Intraday Lows): Min={min(intra_lows)} | Count={len(intra_lows)}")
    else:
        print("🔥 Stage 2.5 (Intraday): NO DATA FOUND")

if __name__ == "__main__":
    targets = find_security_ids()
    for t in targets:
        diagnose_security(t["securityId"], f"{t['strike']} {t['type']}")
