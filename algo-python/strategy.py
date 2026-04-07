import os, requests
from dhan_api import get_option_chain, get_historical_data, get_ltp
from alerts import alert_entry

class StrategyManager:
    def __init__(self, user_id, access_token, client_id, target_price_limit=12.0, 
                 symbol="NIFTY", security_id="13", segment="IDX_I", expiry="",
                 max_daily_loss=5000.0, max_trades_per_day=10, tsl_step=1.0):
        self.user_id = user_id
        self.access_token = access_token
        self.client_id = client_id
        self.target_price_limit = target_price_limit
        self.symbol = symbol
        self.security_id = security_id
        self.segment = segment
        self.expiry = expiry
        
        # Risk Parameters
        self.max_daily_loss = max_daily_loss
        self.max_trades_per_day = max_trades_per_day
        self.tsl_step = tsl_step
        
        self.state = {} # Stores entry search state
        self.active_trades = {} # Stores currently open trades for TSL management
        self.SPRING_URL = os.getenv("SPRING_URL", "http://backend:8080/api/trade")

    def select_best_strikes(self, options):
        best_options = {}
        for opt_type in ['CE', 'PE']:
            # Extra safety: Ensure o is a dict before calling .get()
            eligible = [o for o in options if isinstance(o, dict) and o.get('ltp', 0) <= self.target_price_limit and o.get('optionType') == opt_type]
            print(f">>> [DEBUG] User {self.user_id} {opt_type}: Found {len(eligible)} eligible strikes (Price <= {self.target_price_limit})")
            if eligible:
                best_options[opt_type] = sorted(eligible, key=lambda x: x.get('ltp', 0), reverse=True)[0]
                print(f">>> [DEBUG] User {self.user_id} {opt_type}: Selected Strike {best_options[opt_type].get('strikePrice')} at LTP {best_options[opt_type].get('ltp')}")
        return best_options

    def manage_trailing_sl(self, symbol_key, current_ltp):
        """Logic to move SL up as price moves in profit."""
        trade = self.active_trades[symbol_key]
        entry = trade['entry']
        current_sl = trade['sl']
        
        # If price has moved UP by tsl_step from entry or previous trail point
        # Profit milestones: Entry + Step, Entry + 2*Step, etc.
        # We calculate how many steps we have moved in profit
        profit = current_ltp - entry
        if profit >= self.tsl_step:
            # New calculated SL = Entry + (profit - step)
            # Actually, let's keep it simple: Move SL up by 'tsl_step' for every 'tsl_step' gain
            steps_gained = int(profit / self.tsl_step)
            new_sl = entry + (steps_gained - 1) * self.tsl_step 
            # In LowX2, entry is usually low*2. 
            # Safety: don't let SL go below original SL
            if new_sl > current_sl:
                print(f">>> [TSL] User {self.user_id} {symbol_key} trailing SL from {current_sl} to {new_sl} (LTP: {current_ltp})")
                self.active_trades[symbol_key]['sl'] = new_sl
                self.state[symbol_key]['stopLoss'] = new_sl # Update state for UI

    def process_option_type(self, symbol_key, best_option):
        security_id = best_option['securityId']
        strike = best_option['strikePrice']
        current_ltp = best_option['ltp']

        # 1. Search for Entries if not already in a trade
        if symbol_key not in self.state or self.state[symbol_key]['strike'] != strike:
            if symbol_key in self.state and self.state[symbol_key]['status'] == 'EXECUTED':
                # Already in a trade for this type, skipping search
                pass
            else:
                history = get_historical_data(self.access_token, self.client_id, security_id, self.segment, days=7)
                
                # Robustness: Check if history is a dictionary
                if not isinstance(history, dict):
                    print(f"Error: Historical data is not a dict for {security_id}: {type(history)}")
                    history = {"data": []}
                    
                lows = [c['low'] for c in history.get('data', []) if isinstance(c, dict) and 'low' in c]
                weekly_low = min(lows) if lows else current_ltp
                
                self.state[symbol_key] = {
                    "strike": strike,
                    "securityId": security_id,
                    "low": weekly_low,
                    "entry": weekly_low * 2,
                    "status": "WAITING",
                    "optionType": symbol_key,
                    "stopLoss": max(0.05, weekly_low * 2 - (weekly_low)), # Initial SL
                    "oi": best_option.get('oi', 0),
                    "expiry": self.expiry,
                    "symbol": self.symbol
                }
                print(f"User {self.user_id} tracking {self.symbol} {symbol_key} at Strike {strike}, Entry {weekly_low*2}")
        
        current_live_ltp = get_ltp(self.access_token, self.client_id, security_id)
        self.state[symbol_key]["ltp"] = current_live_ltp # Update Live LTP for UI
        
        # 2. Update Entry if lower price found
        if self.state[symbol_key]["status"] == "WAITING" and current_live_ltp < self.state[symbol_key]["low"]:
            self.state[symbol_key]["low"] = current_live_ltp
            self.state[symbol_key]["entry"] = current_live_ltp * 2
            self.state[symbol_key]["stopLoss"] = max(0.05, current_live_ltp * 2 - current_live_ltp)
            self.state[symbol_key]["oi"] = best_option.get('oi', 0) # Refresh OI
            print(f"User {self.user_id} updated LOW for {symbol_key} to {current_live_ltp}")

        # 3. Handle Entry Execution
        entry_price = self.state[symbol_key]["entry"]
        if current_live_ltp >= entry_price and self.state[symbol_key]["status"] == "WAITING":
            sl = self.state[symbol_key]["stopLoss"]
            self.send_signal(best_option, entry_price, sl)
            self.state[symbol_key]["status"] = "EXECUTED"
            self.active_trades[symbol_key] = {
                "entry": entry_price,
                "sl": sl,
                "securityId": security_id
            }
            alert_entry(self.symbol, strike, entry_price)

        # 4. Manage Trailing Stop Loss for Active Trades
        if symbol_key in self.active_trades:
            self.manage_trailing_sl(symbol_key, current_live_ltp)
            # Check for SL Exit
            if current_live_ltp <= self.active_trades[symbol_key]['sl']:
                print(f">>> [EXIT] User {self.user_id} {symbol_key} SL Hit at {current_live_ltp}")
                # Notify backend (optional, but good for record)
                del self.active_trades[symbol_key]
                self.state[symbol_key]['status'] = 'EXITED_SL'

    def run_strategy(self):
        data = get_option_chain(self.access_token, self.client_id, self.security_id, self.segment, self.expiry)
        
        # Robustness: Check if data is a dictionary
        if not isinstance(data, dict):
            print(f"Error: Option chain data is not a dict: {type(data)}")
            data = {"data": []}
            
        options = data.get('data', []) if isinstance(data, dict) else []
        if not isinstance(options, list):
            print(f"Error: Options data is not a list for user {self.user_id}: {type(options)} - Content: {options}")
            options = []
            
        self.state['option_chain'] = options # Store for UI
        best_options = self.select_best_strikes(options)
        
        if not best_options and not self.active_trades:
            return {"msg": f"No active/eligible logic for user {self.user_id}"}

        for opt_type, best_option in best_options.items():
            self.process_option_type(opt_type, best_option)

        # Also process active trades that might not be in 'best_options' anymore
        for symbol_key in list(self.active_trades.keys()):
            if symbol_key not in best_options:
                current_live_ltp = get_ltp(self.access_token, self.client_id, self.active_trades[symbol_key]['securityId'])
                self.manage_trailing_sl(symbol_key, current_live_ltp)

        return self.state

    def send_signal(self, option, entry, sl):
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
