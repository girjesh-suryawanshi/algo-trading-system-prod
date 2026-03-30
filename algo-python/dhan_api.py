import requests, os
from datetime import datetime, timedelta

BASE_URL = "https://api.dhan.co/v2"

def get_headers(access_token, client_id):
    return {
        "access-token": access_token,
        "client-id": client_id,
        "Content-Type": "application/json"
    }

def get_expiry_list(access_token, client_id, security_id, segment="IDX_I"):
    url = f"{BASE_URL}/optionchain/expirylist"
    payload = {
        "UnderlyingScrip": int(security_id),
        "UnderlyingSeg": segment
    }
    try:
        res = requests.post(url, json=payload, headers=get_headers(access_token, client_id), timeout=10)
        if res.status_code == 200:
            return res.json().get('data', [])
        print(f"Dhan API Error (Expiry List): {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Error fetching expiry list: {e}")
    return []

def get_option_chain(access_token, client_id, security_id, segment, expiry):
    url = f"{BASE_URL}/optionchain"
    payload = {
        "UnderlyingScrip": int(security_id),
        "UnderlyingSeg": segment,
        "Expiry": expiry
    }
    try:
        res = requests.post(url, json=payload, headers=get_headers(access_token, client_id), timeout=10)
        if res.status_code == 200:
            return res.json()
        print(f"Dhan API Error (Option Chain): {res.status_code} - {res.text}")
        return {"data": []}
    except Exception as e:
        print(f"Error fetching option chain: {e}")
        return {"data": []}

def get_historical_data(access_token, client_id, security_id, segment, days=7):
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    url = f"{BASE_URL}/charts/historical"
    payload = {
        "securityId": str(security_id),
        "exchangeSegment": segment,
        "instrument": "OPTIDX",
        "interval": "1",
        "fromDate": from_date,
        "toDate": to_date
    }
    try:
        res = requests.post(url, json=payload, headers=get_headers(access_token, client_id), timeout=10)
        if res.status_code == 200:
            return res.json()
        print(f"Dhan API Error (Historical): {res.status_code} - {res.text}")
        return {"data": []}
    except Exception as e:
        print(f"Error fetching historical: {e}")
        return {"data": []}

def get_ltp(access_token, client_id, security_id):
    url = f"{BASE_URL}/marketquote/ohlc/{security_id}"
    try:
        res = requests.get(url, headers=get_headers(access_token, client_id), timeout=5)
        if res.status_code == 200:
            return res.json().get('data', {}).get('ltp', 0)
        return 0
    except Exception:
        return 0
