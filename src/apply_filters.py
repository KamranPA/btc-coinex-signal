import json

def evaluate_all(df):
    with open('config/settings.json') as f:
        config = json.load(f)
    f = config['filters']
    l = df.iloc[-1]
    p = df.iloc[-2]

    return {
        "trend": l['ema20'] > l['ema50'] > l['ema200'],
        "price_above_ema200": l['close'] > l['ema200'],
        "volume_spike": l['volume'] > f['min_volume_multiplier'] * df['volume'].tail(20).mean(),
        "high_volatility": l['atr'] > f['min_atr_multiplier'] * l['close'],
        "rsi_ok": 30 < l['rsi'] < 70,
        "structure": l['low'] > p['low'] if l['close'] > l['open'] else False
    }
