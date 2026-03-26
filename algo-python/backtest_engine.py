import pandas as pd
from strategy import select_best_strike

def run_backtest(historical_data):
    """
    Simulates trades based on historical data.
    Input: DataFrame with columns [timestamp, strike, type, open, high, low, close, volume]
    """
    trades = []
    equity_curve = [100000] # Start with 1L capital
    
    # Simple simulation logic
    # For each day/period, identify the 'Low' and check for break
    # This is a simplified version for demonstration
    
    # Group by strike
    for strike, group in historical_data.groupby('strike'):
        weekly_low = group['low'].min()
        entry_price = weekly_low * 2
        sl = weekly_low - 1
        target = entry_price + 2*(entry_price - weekly_low) # 1:2 RR
        
        # Check if entry triggered
        triggered = group[group['high'] >= entry_price]
        if not triggered.empty:
            entry_time = triggered.index[0]
            # Check results after entry
            post_entry = group.loc[entry_time:]
            
            # Did it hit SL first or Target?
            hit_sl = post_entry[post_entry['low'] <= sl]
            hit_target = post_entry[post_entry['high'] >= target]
            
            if not hit_sl.empty and (hit_target.empty or hit_sl.index[0] < hit_target.index[0]):
                pnl = (sl - entry_price) * 50 # 1 lot = 50 qty
                trades.append({"strike": strike, "result": "SL", "pnl": pnl})
            elif not hit_target.empty:
                pnl = (target - entry_price) * 50
                trades.append({"strike": strike, "result": "TARGET", "pnl": pnl})
    
    # Calculate metrics
    df_trades = pd.DataFrame(trades)
    win_rate = (df_trades['pnl'] > 0).mean() * 100 if not df_trades.empty else 0
    total_pnl = df_trades['pnl'].sum() if not df_trades.empty else 0
    
    return {
        "win_rate": f"{win_rate:.2f}%",
        "total_pnl": total_pnl,
        "trade_count": len(trades),
        "trades": trades
    }
