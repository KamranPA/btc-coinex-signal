# strategy.py
import numpy as np
import pandas as pd

def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed > 0].sum() / period
    down = -seed[seed < 0].sum() / period
    if down == 0: down = 1e-10
    rs = up / down
    rsi = [100. - 100. / (1. + rs)]
    for i in range(period, len(prices)):
        delta = deltas[i-1]
        upval = delta if delta > 0 else 0
        downval = -delta if delta < 0 else 0
        up = (up * (period-1) + upval) / period
        down = (down * (period-1) + downval) / period
        rs = up / down if down != 0 else 1e-10
        rsi.append(100. - 100. / (1. + rs))
    return np.array(rsi)

def generate_signal(df):
    if len(df) < 200:
        return None

    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    volume = df['volume'].values

    # محاسبه اندیکاتورها
    ema200 = df['close'].ewm(span=200).mean().values
    rsi = calculate_rsi(close, 14)
    vol_ma5 = df['volume'].rolling(5).mean().values

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # شرایط خرید
    if (last['close'] > ema200[-1] and
        last['close'] > last['open'] and  # کندل سبز
        (rsi[-2] < 45 or rsi[-3] < 45) and
        volume[-1] > vol_ma5[-1]):

        entry = last['close']
        sl = min(low[-3:]) * 0.995
        tp = entry + 2 * (entry - sl)
        return {
            'type': 'BUY',
            'entry': round(entry, 4),
            'sl': round(sl, 4),
            'tp': round(tp, 4),
            'rsi': round(rsi[-1], 1),
            'volume_ratio': round(volume[-1] / vol_ma5[-1], 2)
        }

    # شرایط فروش (اختیاری)
    elif (last['close'] < ema200[-1] and
          last['close'] < last['open'] and  # کندل قرمز
          (rsi[-2] > 55 or rsi[-3] > 55) and
          volume[-1] > vol_ma5[-1]):

        entry = last['close']
        sl = max(high[-3:]) * 1.005
        tp = entry - 2 * (sl - entry)
        return {
            'type': 'SELL',
            'entry': round(entry, 4),
            'sl': round(sl, 4),
            'tp': round(tp, 4),
            'rsi': round(rsi[-1], 1),
            'volume_ratio': round(volume[-1] / vol_ma5[-1], 2)
        }

    return None
