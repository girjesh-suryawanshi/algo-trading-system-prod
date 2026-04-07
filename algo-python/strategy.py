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
        """Identify all strike prices where LTP <= 12."""
        eligible = [o for o in options if isinstance(o, dict) and o.get('ltp', 0) <= self.target_price_limit and o.get('ltp', 0) > 0]
        print(f">>> [DEBUG] User {self.user_id}: Found {len(eligible)} strikes (Price <= {self.target_price_limit})")
        
        # Sort by LTP descending to pick the most relevant one (closest to 12)
        # But per Rule #7, we only track ONE pending order at a time across CE/PE.
        if not eligible:
            return None
            
        best = sorted(eligible, key=lambda x: x.get('ltp', 0), reverse=True)[0]
        return best

    def process_strategy_logic(self):
        """Main loop for strategy execution according to User rules."""
        data = get_option_chain(self.access_token, self.client_id, self.security_id, self.segment, self.expiry)
        options = data.get('data', []) if isinstance(data, dict) else []
        self.state['option_chain'] = options

        # 1. Handle Active (Executed) Trades Independently (Rule #8)
        for symbol_key in list(self.active_trades.keys()):
            trade = self.active_trades[symbol_key]
            # Fetch current LTP for active trades
            current_live_ltp = get_ltp(self.access_token, self.client_id, trade['securityId'])
            if current_live_ltp <= 0: continue
            
            self.state[symbol_key]["ltp"] = current_live_ltp
            
            # Check Target/SL
            if current_live_ltp >= trade['target']:
                print(f">>> [EXIT] User {self.user_id} {symbol_key} Target Hit at {current_live_ltp}")
                self.state[symbol_key]['status'] = 'EXITED_TARGET'
                del self.active_trades[symbol_key]
            elif current_live_ltp <= trade['sl']:
                print(f">>> [EXIT] User {self.user_id} {symbol_key} SL Hit at {current_live_ltp}")
                self.state[symbol_key]['status'] = 'EXITED_SL'
                del self.active_trades[symbol_key]

        # 2. Continuous Scanning for New Opportunities (Rule #7)
        best_qualified = self.select_best_strikes(options)
        
        if best_qualified:
            strike = best_qualified['strikePrice']
            security_id = best_qualified['securityId']
            current_ltp = best_qualified['ltp']
            opt_type = best_qualified['optionType']
            
            # If we already have a pending strike, check if it's the same or if we should replace it
            current_pending = self.state.get("PENDING_SIGNAL")
            
            if not current_pending or current_pending['strike'] != strike or current_pending['optionType'] != opt_type:
                # Rule #7: Cancel previous pending signal if not executed
                if current_pending:
                    self.cancel_pending_signal(current_pending)
                
                # Fetch Contract-lifetime LOW (30 days)
                history = get_historical_data(self.access_token, self.client_id, security_id, self.segment, days=30)
                lows = [c['low'] for c in history.get('data', []) if isinstance(c, dict) and 'low' in c]
                contract_low = min(lows) if lows else current_ltp
                
                entry_price = contract_low * 2
                sl_price = contract_low - 1
                risk = entry_price - sl_price
                
                new_signal = {
                    "strike": strike,
                    "securityId": security_id,
                    "low": contract_low,
                    "entry": entry_price,
                    "stopLoss": sl_price,
                    "target": round(entry_price + (2 * risk), 2), # Default to 1:2 per logic
                    "optionType": opt_type,
                    "status": "WAITING",
                    "symbol": self.symbol,
                    "expiry": self.expiry,
                    "ltp": current_ltp
                }
                
                # Send Signal to Backend (Rule #3: Create Pending Order)
                self.send_signal(new_signal)
                self.state["PENDING_SIGNAL"] = new_signal
                self.state[opt_type] = new_signal # For UI display
                
            else:
                # Same strike, just update LTP
                self.state["PENDING_SIGNAL"]["ltp"] = current_ltp
                self.state[opt_type]["ltp"] = current_ltp
                
                # Check for Execution (Rule #6: LTP hits Entry)
                # Note: In real setup, the broker handles the pending order. 
                # We track it here to move it to 'active_trades' once we detect execution.
                if current_ltp >= self.state["PENDING_SIGNAL"]["entry"]:
                    pending = self.state["PENDING_SIGNAL"]
                    self.active_trades[opt_type] = {
                        "entry": pending["entry"],
                        "sl": pending["stopLoss"],
                        "target": pending["target"],
                        "securityId": pending["securityId"]
                    }
                    self.state[opt_type]["status"] = "EXECUTED"
                    del self.state["PENDING_SIGNAL"]
                    alert_entry(self.symbol, pending["strike"], pending["entry"])

        return self.state

    def run_strategy(self):
        # Update India VIX
        from dhan_api import get_india_vix
        real_vix = get_india_vix(self.access_token, self.client_id)
        if real_vix is not None:
            self.state['indiaVix'] = round(real_vix, 2)
            
        return self.process_strategy_logic()

    def send_signal(self, signal):
        """Sends signal to backend to place PENDING order."""
        payload = {
            "symbol": signal['symbol'],
            "strike": signal['strike'],
            "optionType": signal['optionType'],
            "entryPrice": signal['entry'],
            "stopLoss": signal['stopLoss'],
            "target1": signal['target'],
            "qty": 50,
            "strategyName": "LowX2",
            "userId": self.user_id,
            "isPending": True # Hint to backend to use LIMIT order
        }
        try:
            headers = {"X-Engine-Token": "lumina-secret-2026"}
            engine_url = self.SPRING_URL.replace("/trade", "/engine/signal")
            requests.post(engine_url, json=payload, headers=headers, timeout=3)
            print(f"Signal sent for {signal['optionType']} {signal['strike']} (Pending at {signal['entry']})")
        except Exception as e:
            print(f"Failed to send signal: {e}")

    def cancel_pending_signal(self, signal):
        """Notifies backend to cancel existing pending order."""
        payload = {
            "symbol": signal['symbol'],
            "strike": signal['strike'],
            "optionType": signal['optionType'],
            "userId": self.user_id
        }
        try:
            headers = {"X-Engine-Token": "lumina-secret-2026"}
            cancel_url = self.SPRING_URL.replace("/trade", "/engine/cancel")
            requests.post(cancel_url, json=payload, headers=headers, timeout=3)
            print(f"Cancellation sent for {signal['optionType']} {signal['strike']}")
        except Exception as e:
            print(f"Failed to cancel signal: {e}")
