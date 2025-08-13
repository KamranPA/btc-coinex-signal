# src/calculate_risk.py
def calculate(df, entry_price, direction="long"):
    l = df.iloc[-1]
    atr = l['atr']
    
    if direction == "long":
        support = df['low'].rolling(10).min().iloc[-1]
        sl = min(entry_price - (1.5 * atr), support * 0.99)
        tp = entry_price + 2 * (entry_price - sl)
        rr = (tp - entry_price) / (entry_price - sl) if entry_price > sl else 0
    else:
        resistance = df['high'].rolling(10).max().iloc[-1]
        sl = max(entry_price + (1.5 * atr), resistance * 1.01)
        tp = entry_price - 2 * (sl - entry_price)
        rr = (entry_price - tp) / (sl - entry_price) if sl > entry_price else 0

    return {
        "sl": round(sl, 2),
        "tp": round(tp, 2),
        "risk_reward": round(rr, 2),
        "rr_ok": rr >= 1.8
    }
