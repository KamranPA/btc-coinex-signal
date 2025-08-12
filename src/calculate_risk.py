def calculate(df, entry, direction="long"):
    l = df.iloc[-1]
    atr = l['atr']
    support = df['low'].rolling(10).min().iloc[-1]
    resistance = df['high'].rolling(10).max().iloc[-1]

    if direction == "long":
        sl = min(entry - (1.5 * atr), support * 0.99)
        tp = entry + 2 * (entry - sl)
        rr = (tp - entry) / (entry - sl)
    else:
        sl = max(entry + (1.5 * atr), resistance * 1.01)
        tp = entry - 2 * (sl - entry)
        rr = (entry - tp) / (sl - entry)

    return {
        "sl": round(sl, 2),
        "tp": round(tp, 2),
        "risk_reward": round(rr, 2),
        "rr_ok": rr >= config['risk']['min_rr']
    }
