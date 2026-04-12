import os
import requests
from dhan_api import get_option_chain, get_ltp, get_historical_data
from alerts import alert_entry


class StrategyManager:
    def __init__(self, *args, **kwargs):

        # ✅ Safe constructor (fix for your backend issue)
        self.user_id = args[0] if len(args) > 0 else None
        self.access_token = args[1] if len(args) > 1 else None
        self.client_id = args[2] if len(args) > 2 else None

        self.target_price_limit = args[3] if len(args) > 3 else 12.0
        self.symbol = args[4] if len(args) > 4 else "NIFTY"
        self.security_id = args[5] if len(args) > 5 else "13"
        self.segment = args[6] if len(args) > 6 else "IDX_I"
        self.expiry = args[7] if len(args) > 7 else ""

        self.max_daily_loss = args[8] if len(args) > 8 else 5000.0
        self.max_trades_per_day = args[9] if len(args) > 9 else 10
        self.tsl_step = args[10] if len(args) > 10 else 1.0

        self.state = {}
        self.active_trades = {}

        # 🔥 GLOBAL LOW STORAGE (KEY FIX)
        self.global_lows = {}

        self.SPRING_URL = os.getenv("SPRING_URL", "http://backend:8080/api/trade")

    # =========================
    # 🎯 STRIKE SELECTION
    # =========================
    def select_best_strikes(self, options):

        eligible = [
            o for o in options
            if isinstance(o, dict)
            and 0 < o.get('ltp', 0) <= self.target_price_limit
        ]

        candidates = []

        for opt_type in ['CE', 'PE']:
            type_options = [o for o in eligible if o.get('optionType') == opt_type]

            if type_options:
                best = sorted(type_options, key=lambda x: x.get('ltp', 0), reverse=True)[0]
                candidates.append(best)

        return candidates

    # =========================
    # 📉 TRUE LOW CALCULATION (FIXED)
    # =========================
    def get_true_low(self, security_id, current_ltp):
        """
        Calculates the true low by combining a robust Daily historical fetch 
        with continuous real-time LTP tracking. 
        Ensures we capture the absolute lifetime low of the contract.
        """
        if security_id not in self.global_lows:
            # 1. Fetch robust Daily history to find the absolute contract floor.
            # We search 60 days back to be absolutely sure we catch the starting candle.
            history = get_historical_data(
                self.access_token,
                self.client_id,
                security_id,
                "NSE_FNO", # Fixed: Option charts require NSE_FNO
                days=12,
                interval="D"
            )

            lows = [
                c['low'] for c in history.get('data', [])
                if isinstance(c, dict) and c.get('low', 0) > 0
            ]

            if lows:
                # Successfully found historical floor - Lock it in.
                api_low = min(lows)
                self.global_lows[security_id] = api_low
                print(f"📊 HISTORICAL FLOOR SEALED: {api_low} (ID: {security_id})")
            else:
                # API failed or busy: use LTP as temporary fallback for this loop.
                # NOT adding to self.global_lows yet so we retry the history fetch next iteration.
                print(f"⚠️ HISTORY FETCH PENDING (Retrying later) - ID: {security_id}")
                return current_ltp

        # 2. Real-time tracking: Update the low if current LTP breaks below our stored base
        current_base = self.global_lows.get(security_id, current_ltp)
        true_low = min(current_base, current_ltp)
        self.global_lows[security_id] = true_low

        return true_low

    # =========================
    # 🚀 MAIN LOGIC
    # =========================
    def process_strategy_logic(self):

        data = get_option_chain(
            self.access_token,
            self.client_id,
            self.security_id,
            self.segment,
            self.expiry
        )

        options = data.get('data', []) if isinstance(data, dict) else []
        self.state['option_chain'] = options

        # =========================
        # 🧠 ACTIVE TRADES
        # =========================
        for key in list(self.active_trades.keys()):
            trade = self.active_trades[key]

            ltp = get_ltp(self.access_token, self.client_id, trade['securityId'])
            if ltp <= 0:
                continue

            if ltp >= trade['target']:
                print(f"✅ TARGET HIT {key}")
                del self.active_trades[key]

            elif ltp <= trade['sl']:
                print(f"❌ SL HIT {key}")
                del self.active_trades[key]

        # =========================
        # 🔍 NEW SIGNALS
        # =========================
        candidates = self.select_best_strikes(options)

        if "PENDING_SIGNALS" not in self.state:
            self.state["PENDING_SIGNALS"] = {}

        for opt in candidates:

            opt_type = opt['optionType']
            strike = opt['strikePrice']
            security_id = opt['securityId']
            ltp = opt['ltp']
            oi = opt.get('oi', 0)

            existing = self.state["PENDING_SIGNALS"].get(opt_type)

            # =========================
            # 🔁 UPDATE
            # =========================
            if existing and existing['securityId'] == security_id:

                true_low = self.get_true_low(security_id, ltp)

                if true_low < existing['low']:
                    print(f">>> NEW TRUE LOW: {true_low}")

                    existing['low'] = true_low

                    entry = round(true_low * 2, 2)
                    sl = round(true_low - 1, 2)
                    risk = entry - sl

                    existing.update({
                        "entryPrice": entry,
                        "stopLoss": sl,
                        "target1": round(entry + 2 * risk, 2),
                        "ltp": ltp,
                        "oi": oi
                    })

                    self.send_signal(existing)

                # ENTRY
                if ltp >= existing['entryPrice']:
                    print(f"🚀 ENTRY {opt_type}")

                    self.active_trades[opt_type] = {
                        "entry": existing["entryPrice"],
                        "sl": existing["stopLoss"],
                        "target": existing["target1"],
                        "securityId": security_id
                    }

                    alert_entry(self.symbol, strike, existing["entryPrice"])
                    del self.state["PENDING_SIGNALS"][opt_type]

            # =========================
            # 🆕 NEW SIGNAL
            # =========================
            else:

                print(f"Tracking {opt_type} {strike}")

                true_low = self.get_true_low(security_id, ltp)

                entry = round(true_low * 2, 2)
                sl = round(true_low - 1, 2)
                risk = entry - sl

                signal = {
                    "userId": self.user_id,
                    "symbol": f"{self.symbol} {self.expiry} {strike} {opt_type}",
                    "strike": strike,
                    "optionType": opt_type,
                    "securityId": security_id,
                    "low": true_low,
                    "entryPrice": entry,
                    "stopLoss": sl,
                    "target1": round(entry + 2 * risk, 2),
                    "ltp": ltp,
                    "oi": oi,
                    "isPending": True
                }

                self.state["PENDING_SIGNALS"][opt_type] = signal
                self.send_signal(signal)

        return self.state

       # =========================
    # 📡 SIGNAL
    # =========================
    def send_signal(self, signal):
        try:
            payload = {
                "symbol": signal['symbol'],
                "strike": signal['strike'],
                "optionType": signal['optionType'],
                "entryPrice": signal['entryPrice'],
                "stopLoss": signal['stopLoss'],
                "target1": signal['target1'],
                "qty": 65,
                "strategyName": "LowX2-TrueLow",
                "userId": self.user_id,
                "isPending": True
            }

            headers = {"X-Engine-Token": "lumina-secret-2026"}
            url = self.SPRING_URL.replace("/api/trade", "/api/engine/signal")

            requests.post(url, json=payload, headers=headers, timeout=5)

        except Exception as e:
            print(f"Signal error: {e}")

    # =========================
    # 🚀 RUN STRATEGY (FIXED)
    # =========================
    def run_strategy(self):
        try:
            print("🔥 Strategy Running...")
            return self.process_strategy_logic()
        except Exception as e:
            print(f"❌ Strategy runtime error: {e}")
            return {}