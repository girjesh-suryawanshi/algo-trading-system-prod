import requests
import json

ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc2NTMwMjM0LCJpYXQiOjE3NzY0NDM4MzQsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTAxNDYzNzIzIn0.6bmb_2isZlzacZ1rtFAfr5OHFtFC1Nz-WuJTTYdwH9S7KpDF7sa1qy0qig0Ayvbpj99h6GchDPzyeXOy2XvRhw"
CLIENT_ID = "1101463723"
BASE_URL = "https://api.dhan.co/v2"

def get_headers():
    return {
        "access-token": ACCESS_TOKEN,
        "client-id": CLIENT_ID,
        "Content-Type": "application/json"
    }

def debug_chain():
    url = f"{BASE_URL}/optionchain"
    payload = {
        "UnderlyingScrip": 13,
        "UnderlyingSeg": "IDX_I",
        "Expiry": "2026-04-21"
    }
    res = requests.post(url, json=payload, headers=get_headers())
    print(f"Option Chain HTTP Status: {res.status_code}")
    if res.status_code == 200:
        data = res.json()
        oc = data.get("data", {}).get("oc", {})
        print(f"Total Strikes Found: {len(oc)}")
        # Print first few keys
        print(f"Sample Strikes: {list(oc.keys())[:5]}")
        
        # Search for 24950
        for s in oc:
            if "24950" in s or "23500" in s:
                print(f"FOUND MATCH: Strike {s} -> {oc[s]}")

if __name__ == "__main__":
    debug_chain()
