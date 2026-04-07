import requests, os
from datetime import datetime, timedelta

BASE_URL = "https://api.dhan.co/v2"

def get_headers(access_token, client_id):
    return {
        "access-token": access_token,
        "client-id": client_id,
        "Content-Type": "application/json"
    }

def _safe_json(res, default_val=None):
    if default_val is None:
        default_val = {"data": []}
    try:
        data = res.json()
        if isinstance(data, dict):
            return data
        print(f"Unexpected JSON response type: {type(data)} - {data}")
        return default_val
    except Exception as e:
        print(f"JSON Parse Error: {e} - Response Text: {res.text[:100]}")
        return default_val

def get_expiry_list(access_token, client_id, security_id, segment="IDX_I"):
    url = f"{BASE_URL}/optionchain/expirylist"
    payload = {
        "UnderlyingScrip": int(security_id),
        "UnderlyingSeg": segment
    }
    try:
        res = requests.post(url, json=payload, headers=get_headers(access_token, client_id), timeout=10)
        if res.status_code == 200:
            data = _safe_json(res)
            if isinstance(data, dict):
                return data.get('data', [])
            return []
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
            data = _safe_json(res)
            # Official V2 structure: data['data']['oc']
            data_obj = data.get('data', {})
            oc_dict = data_obj.get('oc', {})
            
            # Normalization: If it's a dictionary keyed by strike prices, flatten it
            if isinstance(oc_dict, dict):
                flattened = []
                for strike_str, pairs in oc_dict.items():
                    try:
                        strike_price = float(strike_str)
                        for opt_key, info in pairs.items():
                            if isinstance(info, dict):
                                flattened.append({
                                    'strikePrice': strike_price,
                                    'ltp': info.get('last_price', 0),
                                    'optionType': opt_key.upper(),
                                    'securityId': info.get('security_id'),
                                    'volume': info.get('volume', 0),
                                    'oi': info.get('oi', 0)
                                })
                    except (ValueError, TypeError):
                        continue
                return {'data': flattened}
            return data
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
            return _safe_json(res)
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
            data_resp = _safe_json(res, default_val={"data": {}})
            data = data_resp.get('data', {})
            # Dhan V2 Market Quote OHLC usually returns 'last_price'
            val = data.get('last_price') or data.get('ltp') or data.get('lastPrice') or data.get('close') or 0
            if val == 0:
                print(f"Warning: LTP for {security_id} returned 0. Raw Data: {data}")
            return val
        else:
            print(f"Error: LTP API for {security_id} failed with {res.status_code}")
        return 0
    except Exception as e:
        print(f"Exception in get_ltp: {e}")
        return 0

def get_india_vix(access_token, client_id):
    # India VIX Security ID is 21, Segment Nse_Indices (IDX_I)
    url = f"{BASE_URL}/marketquote/ohlc/21"
    try:
        res = requests.get(url, headers=get_headers(access_token, client_id), timeout=5)
        if res.status_code == 200:
            data_resp = _safe_json(res, default_val={"data": {}})
            data = data_resp.get('data', {})
            val = data.get('last_price') or data.get('ltp') or data.get('lastPrice') or data.get('close')
            if val is not None:
                return float(val)
            print(f"Warning: VIX fetch returned None. Raw Data: {data}")
        else:
            print(f"Error: VIX API failed with {res.status_code}: {res.text}")
        return None # Return None to indicate failure
    except Exception as e:
        print(f"Exception in get_india_vix: {e}")
        return None
