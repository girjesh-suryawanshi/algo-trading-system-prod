import requests, os
from datetime import datetime, timedelta

BASE_URL = "https://api.dhan.co"

def get_headers(access_token, client_id):
    return {
        "access-token": access_token,
        "client-id": client_id,
        "Content-Type": "application/json"
    }

def get_option_chain(access_token, client_id, symbol="NIFTY"):
    url = f"{BASE_URL}/option-chain?symbol={symbol}"
    try:
        res = requests.get(url, headers=get_headers(access_token, client_id), timeout=5)
        if res.status_code == 200:
            return res.json()
        raise Exception(f"API Error: {res.status_code}")
    except Exception as e:
        print(f"Error fetching option chain: {e}")
        return {"data": []}

def get_historical_data(access_token, client_id, security_id, days=7):
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    url = f"{BASE_URL}/charts/historical"
    payload = {
        "securityId": security_id,
        "exchangeSegment": "NSE_FNO",
        "instrument": "OPTIDX",
        "interval": "1",
        "fromDate": from_date,
        "toDate": to_date
    }
    try:
        res = requests.post(url, json=payload, headers=get_headers(access_token, client_id), timeout=5)
        if res.status_code == 200:
            return res.json()
        raise Exception(f"API Error: {res.status_code}")
    except Exception as e:
        print(f"Error fetching historical: {e}")
        return {"data": []}

def get_ltp(access_token, client_id, security_id):
    url = f"{BASE_URL}/market-quote/{security_id}"
    try:
        res = requests.get(url, headers=get_headers(access_token, client_id), timeout=3)
        return res.json().get('data', {}).get('ltp', 0)
    except Exception:
        return 0.0
