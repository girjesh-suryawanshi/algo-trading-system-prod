import pandas as pd
import numpy as np

def run_backtest(df):
    if df.empty or 'timestamp' not in df.columns or 'optionType' not in df.columns:
        return {"error": "Invalid dataframe format for backtest. Need timestamp, strike, optionType, close, low, high"}

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')

    trades = []
    equity = 100000.0
    equity_curve = [{"timestamp": df['timestamp'].iloc[0].isoformat(), "equity": equity}]

    state = {}
    active_trades = []
    timestamps = df['timestamp'].unique()

    for t in timestamps:
        snapshot = df[df['timestamp'] == t]
        current_time = pd.to_datetime(t)

        for trade in active_trades[:]:
            try:
                row = snapshot[(snapshot['strike'] == trade['strike']) & (snapshot['optionType'] == trade['optionType'])]
                if row.empty: continue
                if isinstance(row, pd.DataFrame): row = row.iloc[0]

                if current_time.hour == 15 and current_time.minute >= 15:
                    trade['result'] = 'EOD_SQUAREOFF'
                    pnl = float((row['close'] - trade['entry']) * trade['qty'])
                    trade['pnl'] = pnl
                    trade['exit_time'] = str(t.isoformat())
                    trade['exit_price'] = float(row['close'])
                    trades.append(trade)
                    active_trades.remove(trade)
                    continue

                if row['low'] <= trade['sl']:
                    trade['result'] = 'SL'
                    pnl = float((trade['sl'] - trade['entry']) * trade['qty'])
                    trade['pnl'] = pnl
                    trade['exit_time'] = str(t.isoformat())
                    trade['exit_price'] = float(trade['sl'])
                    trades.append(trade)
                    active_trades.remove(trade)
                elif row['high'] >= trade['target3']:
                    trade['result'] = 'TARGET'
                    pnl = float((trade['target3'] - trade['entry']) * trade['qty'])
                    trade['pnl'] = pnl
                    trade['exit_time'] = str(t.isoformat())
                    trade['exit_price'] = float(trade['target3'])
                    trades.append(trade)
                    active_trades.remove(trade)
            except Exception as e:
                pass

        if 9 <= current_time.hour <= 12 and (current_time.hour > 9 or current_time.minute >= 20):
            for opt_type in ['CE', 'PE']:
                if any(tr['optionType'] == opt_type for tr in active_trades):
                    continue
                
                eligible = snapshot[(snapshot['close'] <= 12) & (snapshot['optionType'] == opt_type)]
                if eligible.empty: continue
                
                best_option = eligible.loc[eligible['close'].idxmax()] if isinstance(eligible, pd.DataFrame) else eligible
                
                strike = int(best_option['strike'])
                close_px = float(best_option['close'])
                
                if opt_type not in state or state[opt_type]['strike'] != strike:
                    historical_floor = float(best_option['historical_floor']) if 'historical_floor' in best_option else 999999.0
                    weekly_low = min(close_px, historical_floor)
                    state[opt_type] = {
                        "strike": strike,
                        "low": weekly_low,
                        "entry": float(weekly_low * 2),
                        "status": "WAITING",
                        "optionType": str(opt_type)
                    }
                
                current_live_ltp = float(best_option['close'])
                if state[opt_type]['status'] == 'WAITING' and current_live_ltp < state[opt_type]['low']:
                    state[opt_type]['low'] = current_live_ltp
                    state[opt_type]['entry'] = float(current_live_ltp * 2)
                
                if current_live_ltp >= state[opt_type]['entry'] and state[opt_type]['status'] == "WAITING":
                    sl = float(max(0.05, state[opt_type]['low'] - 1))
                    risk = float(state[opt_type]['entry'] - sl)
                    
                    new_trade = {
                        "strike": strike,
                        "optionType": str(opt_type),
                        "entry": float(state[opt_type]['entry']),
                        "sl": sl,
                        "target1": float(round(state[opt_type]['entry'] + risk, 2)),
                        "target2": float(round(state[opt_type]['entry'] + 2*risk, 2)),
                        "target3": float(round(state[opt_type]['entry'] + 3*risk, 2)),
                        "entry_time": str(t.isoformat()),
                        "qty": 50,
                        "pnl": 0.0
                    }
                    active_trades.append(new_trade)
                    state[opt_type]['status'] = "EXECUTED"

        if trades and trades[-1]['exit_time'] == str(t.isoformat()):
            total_realized = float(sum(tr.get('pnl', 0.0) for tr in trades))
            equity_curve.append({"timestamp": str(t.isoformat()), "equity": float(100000 + total_realized)})

    df_trades = pd.DataFrame(trades)
    
    if not df_trades.empty:
        win_rate = float((df_trades['pnl'] > 0).mean() * 100)
        total_pnl = float(df_trades['pnl'].sum())
        avg_pnl = float(df_trades['pnl'].mean())
        df_eq = pd.DataFrame(equity_curve)
        rolling_max = df_eq['equity'].cummax()
        drawdown = df_eq['equity'] / rolling_max - 1.0
        max_drawdown = float(drawdown.min() * 100)
    else:
        win_rate = 0.0
        total_pnl = 0.0
        avg_pnl = 0.0
        max_drawdown = 0.0

    return {
        "metrics": {
            "total_trades": int(len(trades)),
            "winning_trades": int((df_trades['pnl'] > 0).sum()) if not df_trades.empty else 0,
            "losing_trades": int((df_trades['pnl'] <= 0).sum()) if not df_trades.empty else 0,
            "win_rate": f"{win_rate:.2f}%",
            "total_pnl": total_pnl,
            "avg_pnl": avg_pnl,
            "max_drawdown": f"{max_drawdown:.2f}%"
        },
        "equity_curve": equity_curve,
        "trades": trades
    }
