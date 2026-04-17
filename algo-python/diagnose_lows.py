import requests
import json
from dhan_api import get_headers, BASE_URL

# REPLACE WITH ACTUAL TOKENS FROM USER
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc2NTMwMjM0LCJpYXQiOjE3NzY0NDM4MzQsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTAxNDYzNzIzIn0.6bmb_2isZlzacZ1rtFAfr5OHFtFC1Nz-WuJTTYdwH9S7KpDF7sa1qy0qig0Ayvbpj99h6GchDPzyeXOy2XvRhw"
CLIENT_ID = "1101463723"

def diagnose_security(security_id):
    print(f"\n--- DIAGNOSING SECURITY ID: {security_id} ---")
    
    # 1. Test marketquote/ohlc
    url_ohlc = f"{BASE_URL}/marketquote/ohlc/{security_id}"
    res_ohlc = requests.get(url_ohlc, headers=get_headers(ACCESS_TOKEN, CLIENT_ID))
    print(f"OHLC Response ({res_ohlc.status_code}): {res_ohlc.text}")
    
    # 2. Test charts/historical
    url_hist = f"{BASE_URL}/charts/historical"
    payload = {
        "securityId": str(security_id),
        "exchangeSegment": "NSE_FNO",
        "instrument": "OPTIDX",
        "interval": "1",
        "fromDate": "2026-04-10",
        "toDate": "2026-04-17"
    }
    res_hist = requests.post(url_hist, json=payload, headers=get_headers(ACCESS_TOKEN, CLIENT_ID))
    print(f"Historical Response ({res_hist.status_code}): {res_hist.text[:500]}...")

if __name__ == "__main__":
    # Get credentials from environment or mock (User needs to approve execution or I'll just check code)
    # Actually, I can't run it without keys. but I'll check the logs of previous runs if available.
    print("Diagnostics ready. Need keys to execute.")
