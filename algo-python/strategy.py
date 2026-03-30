import os, requests
from dhan_api import get_option_chain, get_historical_data, get_ltp
from alerts import alert_entry

class StrategyManager:
    def __init__(self, user_id, access_token, client_id, target_price_limit=12.0, symbol="NIFTY", security_id="13", segment="IDX_I", expiry=""):
        self.user_id = user_id
        self.access_token = access_token
        self.client_id = client_id
        self.target_price_limit = target_price_limit
        self.symbol = symbol
        self.security_id = security_id
        self.segment = segment
        self.expiry = expiry
        self.state = {}
        self.SPRING_URL = os.getenv("SPRING_URL", "http://backend:8080/api/trade")

    def select_best_strikes(self, options):
        best_options = {}
        for opt_type in ['CE', 'PE']:
            eligible = [o for o in options if o.get('ltp', 0) <= self.target_price_limit and o.get('optionType') == opt_type]
            if eligible:
                best_options[opt_type] = sorted(eligible, key=lambda x: x['ltp'], reverse=True)[0]
        return best_options

    def process_option_type(self, symbol_key, best_option):
        security_id = best_option['securityId']
        strike = best_option['strikePrice']
        current_ltp = best_option['ltp']

        if symbol_key not in self.state or self.state[symbol_key]['strike'] != strike:
            if symbol_key in self.state and self.state[symbol_key]['status'] == 'EXECUTED':
                pass
            else:
                history = get_historical_data(self.access_token, self.client_id, security_id, self.segment, days=7)
                lows = [c['low'] for c in history.get('data', [])]
                weekly_low = min(lows) if lows else current_ltp
                
                self.state[symbol_key] = {
                    "strike": strike,
                    "securityId": security_id,
                    "low": weekly_low,
                    "entry": weekly_low * 2,
                    "status": "WAITING",
                    "optionType": symbol_key
                }
                print(f"User {self.user_id} tracking {self.symbol} {symbol_key} at Strike {strike}, Entry {weekly_low*2}")
        
        current_live_ltp = get_ltp(self.access_token, self.client_id, security_id)
        if self.state[symbol_key]["status"] == "WAITING" and current_live_ltp < self.state[symbol_key]["low"]:
            self.state[symbol_key]["low"] = current_live_ltp
            self.state[symbol_key]["entry"] = current_live_ltp * 2
            print(f"User {self.user_id} updated LOW for {symbol_key} to {current_live_ltp}")

        entry_price = self.state[symbol_key]["entry"]
        if current_live_ltp >= entry_price and self.state[symbol_key]["status"] == "WAITING":
            self.send_signal(best_option, entry_price, self.state[symbol_key]["low"])
            self.state[symbol_key]["status"] = "EXECUTED"
            alert_entry(self.symbol, strike, entry_price)

    def run_strategy(self):
        data = get_option_chain(self.access_token, self.client_id, self.security_id, self.segment, self.expiry)
        options = data.get('data', [])
        best_options = self.select_best_strikes(options)
        if not best_options:
            return {"msg": f"No eligible strikes for user {self.user_id} on {self.symbol}"}

        for opt_type, best_option in best_options.items():
            self.process_option_type(opt_type, best_option)

        return self.state

    def send_signal(self, option, entry, low):
        sl = max(0.05, low - 1)
        risk = entry - sl
        payload = {
            "symbol": self.symbol,
            "strike": option['strikePrice'],
            "optionType": option['optionType'],
            "entryPrice": entry,
            "stopLoss": sl,
            "target1": round(entry + risk, 2),
            "target2": round(entry + (2 * risk), 2),
            "target3": round(entry + (3 * risk), 2),
            "qty": 50,
            "strategyName": "LowX2",
            "userId": self.user_id
        }
        try:
            requests.post(self.SPRING_URL, json=payload, timeout=3)
            print(f"Signal sent for User {self.user_id}: {self.symbol} {option['optionType']} {option['strikePrice']}")
        except Exception as e:
            print(f"Failed to send signal for {self.user_id}: {e}")
