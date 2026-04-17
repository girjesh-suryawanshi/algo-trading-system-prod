import requests
import json
from dhan_api import get_headers, BASE_URL

# PLACE WITH ACTUAL TOKENS FROM USER
ACCESS_TOKEN = "USER_KEY" 
CLIENT_ID = "USER_CLIENT_ID"

def diagnose_intraday(security_id):
    print(f"\n--- DIAGNOSING INTRADAY SECURITY ID: {security_id} ---")
    
    url_intraday = f"{BASE_URL}/charts/intraday"
    payload = {
        "securityId": str(security_id),
        "exchangeSegment": "NSE_FNO",
        "instrument": "OPTIDX",
        "interval": "1"
    }
    res_intraday = requests.post(url_intraday, json=payload, headers=get_headers(ACCESS_TOKEN, CLIENT_ID))
    print(f"Intraday Response ({res_intraday.status_code}): {res_intraday.text[:500]}...")

if __name__ == "__main__":
    diagnose_intraday("63482") # Example
