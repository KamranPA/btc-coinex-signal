def calculate_risk(df, entry_price, direction="long"):
    l = df.iloc[-1]
    atr = l['atr']

    if direction == "long":
        sl = entry_price - (1.5 * atr)
        tp = entry_price + 2 * (entry_price - sl)
        rr = (tp - entry_price) / (entry_price - sl)
    else:
        sl = entry_price + (1.5 * atr)
        tp = entry_price - 2 * (sl - entry_price)
        rr = (entry_price - tp) / (sl - entry_price)

    return {
        "sl": round(sl, 2),
        "tp": round(tp, 2),
        "risk_reward": round(rr, 2),
        "rr_ok": rr >= 1.8
    }
