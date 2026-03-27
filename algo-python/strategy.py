import os, requests
from dhan_api import get_option_chain, get_historical_data, get_ltp
from alerts import alert_entry

# State management for active setups
# { "CE": {"strike": 23500, "low": 4.5, "entry": 9.0, "status": "WAITING", ...}, "PE": {...} }
state = {}
SPRING_URL = os.getenv("SPRING_URL", "http://backend:8080/api/trade")

def select_best_strikes(options):
    """
    Select options where premium <= 12, separately for CE and PE.
    Choose the strike with premium closest to 12 (highest among <=12).
    Returns a dict with 'CE' and 'PE' best options.
    """
    best_options = {}
    for opt_type in ['CE', 'PE']:
        eligible = [o for o in options if o.get('ltp', 0) <= 12 and o.get('optionType') == opt_type]
        if eligible:
            best_options[opt_type] = sorted(eligible, key=lambda x: x['ltp'], reverse=True)[0]
    return best_options

def process_option_type(symbol_key, best_option):
    security_id = best_option['securityId']
    strike = best_option['strikePrice']
    current_ltp = best_option['ltp']

    # Initial setup or Strike Switching
    if symbol_key not in state or state[symbol_key]['strike'] != strike:
        if symbol_key in state and state[symbol_key]['status'] == 'EXECUTED':
            # Don't switch if already in a trade for this type
            pass
        else:
            # New strike or better strike available! (Strike Switching)
            history = get_historical_data(security_id, days=7)
            lows = [c['low'] for c in history.get('data', [])]
            weekly_low = min(lows) if lows else current_ltp
            
            state[symbol_key] = {
                "strike": strike,
                "securityId": security_id,
                "low": weekly_low,
                "entry": weekly_low * 2,
                "status": "WAITING",
                "optionType": symbol_key
            }
            print(f"Tracking {symbol_key} at Strike {strike}, Entry {weekly_low*2}")
    
    # Dynamic Update: If new LOW forms before entry
    current_live_ltp = get_ltp(security_id)
    if state[symbol_key]["status"] == "WAITING" and current_live_ltp < state[symbol_key]["low"]:
        state[symbol_key]["low"] = current_live_ltp
        state[symbol_key]["entry"] = current_live_ltp * 2
        print(f"Updated LOW for {symbol_key} to {current_live_ltp}. New Entry: {current_live_ltp * 2}")

    # Entry Trigger
    entry_price = state[symbol_key]["entry"]
    if current_live_ltp >= entry_price and state[symbol_key]["status"] == "WAITING":
        send_signal(best_option, entry_price, state[symbol_key]["low"])
        state[symbol_key]["status"] = "EXECUTED"
        alert_entry("NIFTY", strike, entry_price)


def run_strategy():
    # 1. Fetch Option Chain
    data = get_option_chain(symbol="NIFTY")
    options = data.get('data', [])

    # 2. Select Best Strikes for CE & PE
    best_options = select_best_strikes(options)
    if not best_options:
        return {"msg": "No eligible strikes (LTP > 12) for both CE & PE"}

    # 3. Process each option type tracking independently
    for opt_type, best_option in best_options.items():
        process_option_type(opt_type, best_option)

    return state

def send_signal(option, entry, low):
    # Risk R = Entry - SL
    sl = max(0.05, low - 1)
    risk = entry - sl
    
    payload = {
        "symbol": "NIFTY",
        "strike": option['strikePrice'],
        "optionType": option['optionType'],
        "entryPrice": entry,
        "stopLoss": sl,
        "target1": round(entry + risk, 2),
        "target2": round(entry + (2 * risk), 2),
        "target3": round(entry + (3 * risk), 2),
        "qty": 50,
        "strategyName": "LowX2"
    }
    try:
        requests.post(SPRING_URL, json=payload, timeout=3)
        print(f"Signal sent for {option['optionType']} {option['strikePrice']}")
    except Exception as e:
        print(f"Failed to send signal: {e}")
