import os
import requests
from datetime import datetime, timedelta
from dhan_api import get_option_chain, get_ltp, get_historical_data, get_security_quote, get_intraday_data
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

    def calculate_lookback_horizon(self):
        """
        Calculates the required historical lookback days based on how far away
        the current expiry in the strategy is from Today.
        """
        try:
            if not self.expiry or len(self.expiry) < 8:
                return 15 # Default safe fallback
            
            # Parse expiry date (Format: YYYY-MM-DD)
            expiry_date = datetime.strptime(self.expiry.strip(), "%Y-%m-%d")
            today = datetime.now()
            days_to_expiry = (expiry_date - today).days

            if days_to_expiry <= 7:
                # Current week expiry - but we look back enough to see the full month history if it's a monthly
                return 25 
            elif days_to_expiry <= 14:
                # Next week expiry
                return 35
            else:
                # Monthly or further
                return 60
        except Exception as e:
            print(f"⚠️ Lookback Calculation Error: {e}")
            return 15 # Safe fallback

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
    def get_true_low(self, security_id, current_ltp, session_low=None):
        """
        ULTIMATE EXCHANGE-VERIFIED FLOOR SNIPER (V3)
        Combines 150-day Daily, 45-day High-Res Minute, Option Chain session-low,
        and real-time Market Quote Snapshots to guarantee 100% wick-accuracy.
        """
        if security_id not in self.global_lows:
            print(f"🎯 [ULTIMATE SNIPER V3] Identifying Exchange floors for ID: {security_id}")
            
            all_historical_lows = []
            
            try:
                # --- STAGE 0: REAL-TIME MARKET SNAPSHOT (RAW WICK) ---
                market_quote = get_security_quote(self.access_token, self.client_id, security_id)
                if market_quote.get('low') is not None:
                    all_historical_lows.append(market_quote['low'])
                    print(f"🎯 [MARKET SNAPSHOT LOW] Raw Session Floor: {market_quote['low']} (ID: {security_id})")

                # --- STAGE 1: LIFE-OF-CONTRACT BASELINE (150 DAYS DAILY) ---
                daily_hd = get_historical_data(
                    self.access_token, self.client_id, security_id, "NSE_FNO", 
                    days=150, interval="D"
                )
                if daily_hd and "data" in daily_hd:
                    daily_candles = daily_hd["data"]
                    all_historical_lows.extend([c['low'] for c in daily_candles if isinstance(c, dict) and c.get('low', 0) > 0])

                # --- STAGE 2: DEEP PRECISION SCAN (LAST 150 DAYS) ---
                # We fetch in 5-day chunks for maximum wick recovery across the contract life.
                sequential_errors = 0
                for i in range(30): # 30 chunks * 5 days = 150 days
                    if sequential_errors >= 5:
                        break # Stop scanning if we hit 5 contiguous empty ranges (likely pre-listing)

                    to_d = (datetime.now() - timedelta(days=i*5)).strftime("%Y-%m-%d")
                    from_d = (datetime.now() - timedelta(days=(i+1)*5)).strftime("%Y-%m-%d")
                    
                    try:
                        prec_hd = get_historical_data(
                            self.access_token, self.client_id, security_id, "NSE_FNO",
                            interval="1", from_date_str=from_d, to_date_str=to_d
                        )
                        if prec_hd and isinstance(prec_hd, dict) and "data" in prec_hd:
                            prec_candles = prec_hd["data"]
                            if prec_candles:
                                sequential_errors = 0 # Reset error counter on success
                                all_historical_lows.extend([c['low'] for c in prec_candles if isinstance(c, dict) and c.get('low', 0) > 0])
                            else:
                                sequential_errors += 1
                        else:
                            sequential_errors += 1
                    except Exception as scan_err:
                        print(f"⚠️ [SCAN SKIP] Chunk {i} failed for ID {security_id}: {scan_err}")
                        sequential_errors += 1

                # --- STAGE 2.5: LIVE SESSION SCAN (TODAY'S WICK) ---
                # This recovers the absolute low reached TODAY before the engine started.
                try:
                    intraday_hd = get_intraday_data(self.access_token, self.client_id, security_id, "NSE_FNO")
                    if intraday_hd and "data" in intraday_hd:
                        session_lows = [c['low'] for c in intraday_hd["data"] if isinstance(c, dict) and c.get('low', 0) > 0]
                        if session_lows:
                            absolute_session_low = min(session_lows)
                            all_historical_lows.append(absolute_session_low)
                            print(f"✅ [LIVE SESSION LOW] Absolute Session Wick: {absolute_session_low} (ID: {security_id})")
                except Exception as intra_err:
                    print(f"⚠️ [INTRADAY SCAN FAIL] ID {security_id}: {intra_err}")
                if session_low and float(session_low) > 0:
                    all_historical_lows.append(float(session_low))

                # Final check against current LTP
                all_historical_lows.append(current_ltp)

                # --- FINAL CALCULATION ---
                true_floor = min(all_historical_lows) if all_historical_lows else current_ltp
                self.global_lows[security_id] = true_floor
                
                print(f"✅ [SNIPER SEALED] Absolute Global Floor: {true_floor} (ID: {security_id})")
                return true_floor

            except Exception as e:
                print(f"❌ [SNIPER ERROR] High-Res Fallback: {e}")
                return current_ltp
        
        # 4. LIVE TRACKING: Update global low if session low or LTP drops further
        current_floor = self.global_lows.get(security_id, current_ltp)
        
        comp_values = [current_floor, current_ltp]
        if session_low: comp_values.append(float(session_low))
        
        new_floor = min(comp_values)
        if new_floor < current_floor:
            self.global_lows[security_id] = new_floor
            print(f"📉 [EXCHANGE WICK CAPTURED] Absolute Pivot: {new_floor} (ID: {security_id})")
            
        return self.global_lows[security_id]

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
        # 🧠 ACTIVE TRADES (WITH TRAILING SL)
        # =========================
        for key in list(self.active_trades.keys()):
            trade = self.active_trades[key]

            ltp = get_ltp(self.access_token, self.client_id, trade['securityId'])
            if ltp <= 0:
                continue

            # 🛑 1. CHECK TARGET HIT
            if ltp >= trade['target']:
                print(f"✅ TARGET HIT {key}")
                self.send_exit_signal(trade, "TARGET_HIT", trade['target'])
                del self.active_trades[key]
                continue

            # 🛑 2. CHECK SL HIT (FIXED OR TRAILED)
            if ltp <= trade['sl']:
                print(f"❌ SL HIT {key}")
                self.send_exit_signal(trade, "SL_HIT", trade['sl'])
                del self.active_trades[key]
                continue

            # 📈 3. TRAILING STOP LOSS LOGIC
            # If price reaches Entry + Step, trail SL by Step
            if self.tsl_step > 0:
                # Initialize last_trailed_at if not present
                if "last_trail_ltp" not in trade:
                    trade["last_trail_ltp"] = trade["entry"]

                # Check if price has moved up enough to trigger a trail
                diff = ltp - trade["last_trail_ltp"]
                if diff >= self.tsl_step:
                    num_steps = int(diff // self.tsl_step)
                    trail_amount = num_steps * self.tsl_step
                    
                    old_sl = trade["sl"]
                    trade["sl"] = round(trade["sl"] + trail_amount, 2)
                    trade["last_trail_ltp"] = trade["last_trail_ltp"] + trail_amount
                    
                    print(f"🔄 TRAILING SL: {key} | Moved SL from {old_sl} to {trade['sl']}")
                    
                    # Notify Java Backend of the SL update (for UI sync)
                    self.notify_sl_update(trade)

        # =========================
        # 🔍 NEW SIGNALS (ENTRY)
        # =========================
        candidates = self.select_best_strikes(options)

        if "PENDING_SIGNALS" not in self.state:
            self.state["PENDING_SIGNALS"] = {}

        for opt in candidates:

            opt_type = opt['optionType']
            
            # PREVENT MULTI-EXECUTION BUG:
            # If we already have an active OPEN trade for this side (CE/PE), 
            # do not track new candidates for it until the active one exits.
            if opt_type in self.active_trades:
                continue

            strike = opt['strikePrice']
            security_id = opt['securityId']
            ltp = opt['ltp']
            oi = opt.get('oi', 0)

            existing = self.state["PENDING_SIGNALS"].get(opt_type)

            # =========================
            # 🔁 UPDATE
            # =========================
            if existing and existing['securityId'] == security_id:

                true_low = self.get_true_low(security_id, ltp, session_low=opt.get('lowPrice'))

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
                        "securityId": security_id,
                        "symbol": existing["symbol"],
                        "optionType": opt_type
                    }

                    # Send EXECUTION POST to Java
                    existing["isPending"] = False
                    self.send_signal(existing)

                    alert_entry(self.symbol, strike, existing["entryPrice"])
                    del self.state["PENDING_SIGNALS"][opt_type]

            # =========================
            # 🆕 NEW SIGNAL
            # =========================
            else:

                print(f"Tracking {opt_type} {strike}")

                true_low = self.get_true_low(security_id, ltp, session_low=opt.get('lowPrice'))

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
                    "status": "WAITING",
                    "expiry": self.expiry,
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
                "qty": 75,
                "strategy_name": "LowX2",
                "userId": self.user_id,
                "isPending": signal.get('isPending', True)
            }

            headers = {"X-Engine-Token": "lumina-secret-2026"}
            url = self.SPRING_URL.replace("/api/trade", "/api/engine/signal")

            requests.post(url, json=payload, headers=headers, timeout=5)

        except Exception as e:
            print(f"Signal error: {e}")

    # =========================
    # 🚪 EXIT SIGNAL
    # =========================
    def send_exit_signal(self, trade, status, exit_price):
        try:
            payload = {
                "userId": self.user_id,
                "symbol": trade.get('symbol', 'UNKNOWN'),
                "optionType": trade.get('optionType', 'CE'),
                "status": status,
                "exitPrice": exit_price
            }
            headers = {"X-Engine-Token": "lumina-secret-2026"}
            url = self.SPRING_URL.replace("/api/trade", "/api/engine/exit")
            requests.post(url, json=payload, headers=headers, timeout=5)
        except Exception as e:
            print(f"Exit Signal error: {e}")

    # =========================
    # 🔄 TSL UPDATE NOTIFICATION
    # =========================
    def notify_sl_update(self, trade):
        try:
            payload = {
                "userId": self.user_id,
                "symbol": trade.get('symbol', 'UNKNOWN'),
                "optionType": trade.get('optionType', 'CE'),
                "stopLoss": trade.get('sl')
            }
            headers = {"X-Engine-Token": "lumina-secret-2026"}
            url = self.SPRING_URL.replace("/api/trade", "/api/engine/update")
            requests.post(url, json=payload, headers=headers, timeout=5)
        except Exception as e:
            print(f"TSL Update error: {e}")

    # =========================
    # 🚀 RUN STRATEGY (FIXED)
    # =========================
    def run_strategy(self):
        try:
            return self.process_strategy_logic()
        except Exception as e:
            print(f"❌ Strategy runtime error: {e}")
            return {}