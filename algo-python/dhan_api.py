import requests, os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.dhan.co"
TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "YOUR_TOKEN")

HEADERS = {
    "access-token": TOKEN,
    "Content-Type": "application/json"
}

def get_option_chain(symbol="NIFTY"):
    """
    Fetches the option chain for the given symbol.
    """
    url = f"{BASE_URL}/option-chain?symbol={symbol}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
        raise Exception(f"API Error: {res.status_code}")
    except Exception as e:
        print(f"Error fetching option chain: {e}")
        # fallback dummy data for testing
        return {"data": [
            {"strikePrice": 23500, "optionType": "CE", "ltp": 11.2, "securityId": "1"},
            {"strikePrice": 23500, "optionType": "PE", "ltp": 9.5, "securityId": "2"},
            {"strikePrice": 23600, "optionType": "CE", "ltp": 14.5, "securityId": "3"},
            {"strikePrice": 23400, "optionType": "PE", "ltp": 12.0, "securityId": "4"}
        ]}

def get_historical_data(security_id, days=7):
    """
    Fetches historical data for the last 'days' to compute the LOW.
    """
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
        res = requests.post(url, json=payload, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            return res.json()
        raise Exception(f"API Error: {res.status_code}")
    except Exception as e:
        print(f"Error fetching historical: {e}")
        # fallback dummy: last 7 days low simulation
        return {"data": [{"low": 4.5}, {"low": 5.2}, {"low": 3.9}, {"low": 6.1}]}

def get_ltp(security_id):
    """
    Fetches real-time LTP for a security ID.
    """
    url = f"{BASE_URL}/market-quote/{security_id}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=3)
        return res.json().get('data', {}).get('ltp', 0)
    except Exception:
        return 12.5 # Mock LTP
