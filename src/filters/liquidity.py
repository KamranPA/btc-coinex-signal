def detect_liquidity_grab(df):
    l = df.iloc[-1]
    p = df.iloc[-2]

    body_ratio = abs(p['open'] - p['close']) / (p['high'] - p['low']) if p['high'] != p['low'] else 0

    long = (body_ratio < 0.3) and (l['close'] > l['open']) and (l['volume'] > df['volume'].tail(10).mean() * 1.5)
    short = (body_ratio < 0.3) and (l['close'] < l['open']) and (l['volume'] > df['volume'].tail(10).mean() * 1.5)

    return {"long": long, "short": short}
