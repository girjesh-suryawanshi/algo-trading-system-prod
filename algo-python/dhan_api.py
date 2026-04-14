import requests
import time
import random
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

BASE_URL = "https://api.dhan.co/v2"

# =========================
# 🌐 PERSISTENT SESSION
# =========================
session = requests.Session()
retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
    backoff_factor=1
)
adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
session.mount("https://", adapter)
session.mount("http://", adapter)


# =========================
# 🔐 HEADERS
# =========================
def get_headers(access_token, client_id):
    return {
        "access-token": access_token,
        "client-id": client_id,
        "Content-Type": "application/json"
    }


# =========================
# 🛡️ SAFE JSON
# =========================
def _safe_json(res, default_val=None):
    if default_val is None:
        default_val = {"data": []}

    try:
        data = res.json()
        return data if isinstance(data, dict) else default_val
    except Exception as e:
        print(f"JSON Parse Error: {e} - {res.text[:100]}")
        return default_val


# =========================
# 📆 EXPIRY LIST
# =========================
def get_expiry_list(access_token, client_id, security_id, segment="IDX_I"):
    url = f"{BASE_URL}/optionchain/expirylist"

    payload = {
        "UnderlyingScrip": int(security_id),
        "UnderlyingSeg": segment
    }

    try:
        res = session.post(url, json=payload, headers=get_headers(access_token, client_id), timeout=15)

        if res.status_code == 200:
            data = _safe_json(res)
            return data.get('data', [])
        else:
            print(f"Expiry Error: {res.status_code} - {res.text}")

    except Exception as e:
        print(f"Expiry Exception: {e}")

    return []


# =========================
# 📊 OPTION CHAIN (WORKING)
# =========================
def get_option_chain(access_token, client_id, security_id, segment, expiry):

    url = f"{BASE_URL}/optionchain"

    payload = {
        "UnderlyingScrip": int(security_id),
        "UnderlyingSeg": segment,   # KEEP IDX_I
        "Expiry": expiry            # keep same format as before
    }

    for attempt in range(3):
        try:
            res = session.post(url, json=payload, headers=get_headers(access_token, client_id), timeout=15)

            if res.status_code == 200:
                data = _safe_json(res)
                oc_dict = data.get('data', {}).get('oc', {})
                flattened = []

                for strike_str, pair in oc_dict.items():
                    try:
                        strike = float(strike_str)
                        for opt_type, info in pair.items():
                            if isinstance(info, dict):
                                flattened.append({
                                    "strikePrice": strike,
                                    "ltp": info.get("last_price", 0),
                                    "optionType": opt_type.upper(),
                                    "securityId": info.get("security_id"),
                                    "volume": info.get("volume", 0),
                                    "oi": info.get("oi", 0)
                                })
                    except:
                        continue
                return {"data": flattened}
            
            elif res.status_code == 429:
                wait_time = (2 ** attempt) + random.random()
                print(f"⚠️ Rate limited (429) on Option Chain. Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
                continue

            print(f"Option Chain Error: {res.status_code} - {res.text}")
            return {"data": []}

        except Exception as e:
            print(f"Option Chain Exception: {e}")
            if attempt < 2:
                time.sleep(1)
                continue
            return {"data": []}
    return {"data": []}


# =========================
# 📉 HISTORICAL DATA (SAFE VERSION)
# =========================
def get_historical_data(access_token, client_id, security_id, segment, days=30, interval="1"):

    url = f"{BASE_URL}/charts/historical"

    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    payload = {
        "securityId": str(security_id),
        "exchangeSegment": segment,   # KEEP IDX_I (IMPORTANT)
        "instrument": "OPTIDX",
        "interval": interval,         # KEEP "1" (WORKING IN YOUR SYSTEM)
        "fromDate": from_date,
        "toDate": to_date
    }

    for attempt in range(3):
        try:
            res = session.post(url, json=payload, headers=get_headers(access_token, client_id), timeout=15)

            if res.status_code == 200:
                data = _safe_json(res)
                print(f"🔥 RAW DHAN API HISTORICAL RESPONSE: {data}")
                
                # Check if it's wrapped in 'data' or flat
                charts = data.get("data") if "open" not in data else data
                
                if isinstance(charts, dict):
                    lows_array = charts.get("low", [])
                    candles = [{"low": float(l)} for l in lows_array if l and float(l) > 0]
                else:
                    candles = []
                    
                return {"data": candles}
            
            elif res.status_code == 429:
                wait_time = (2 ** attempt) + random.random()
                print(f"⚠️ Rate limited (429) on Historical Data. Retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
                continue

            print(f"Historical Error: {res.status_code} - {res.text}")
            return {"data": []}

        except Exception as e:
            print(f"Historical Exception: {e}")
            if attempt < 2:
                time.sleep(1)
                continue
            return {"data": []}
    return {"data": []}


# =========================
# 💰 LTP (STABLE)
# =========================
def get_ltp(access_token, client_id, security_id):

    url = f"{BASE_URL}/marketquote/ohlc/{security_id}"

    try:
        res = session.get(url, headers=get_headers(access_token, client_id), timeout=15)

        if res.status_code == 200:
            data = _safe_json(res, {"data": {}}).get("data", {})

            ltp = (
                data.get("last_price")
                or data.get("ltp")
                or data.get("lastPrice")
                or data.get("close")
                or 0
            )

            return float(ltp)

        print(f"LTP Error: {res.status_code}")
        return 0

    except Exception as e:
        print(f"LTP Exception: {e}")
        return 0


# =========================
# 📉 INDIA VIX (OPTIONAL)
# =========================
def get_india_vix(access_token, client_id):
    try:
        url = f"{BASE_URL}/marketquote/ohlc/21"

        res = session.get(url, headers=get_headers(access_token, client_id), timeout=15)

        if res.status_code == 200:
            data = _safe_json(res, {"data": {}}).get("data", {})

            val = (
                data.get("last_price")
                or data.get("ltp")
                or data.get("lastPrice")
                or data.get("close")
            )

            return float(val) if val else None

        return None

    except Exception:
        return None