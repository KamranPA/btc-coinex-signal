# risk_management.py
import numpy as np

def find_support_resistance(candles, window=5):
    # پشتیبانی و مقاومت محلی (آخرین 5 کندل)
    lows = candles['low'][-window:]
    highs = candles['high'][-window:]
    support = np.min(lows)
    resistance = np.max(highs)
    return support, resistance

def calculate_fib_levels(high, low):
    diff = high - low
    levels = {
        '0.0': low,
        '0.236': low + 0.236 * diff,
        '0.382': low + 0.382 * diff,
        '0.5': low + 0.5 * diff,
        '0.618': low + 0.618 * diff,
        '1.0': low + diff
    }
    return levels

def get_entry_sl_tp(signal, data):
    close = data['close'].values
    high = data['high'].values
    low = data['low'].values

    last_close = close[-1]
    recent_support, recent_resistance = find_support_resistance(data)

    if signal == "BUY":
        entry = last_close
        sl = min(recent_support, low[-3:].min()) * 0.998  # کمی زیر پشتیبانی
        fib = calculate_fib_levels(recent_resistance, recent_support)
        tp = fib['0.618']  # هدف اول: 61.8% فیبوناچی
        if tp <= entry:
            tp = fib['1.0']  # اگر فیب منطقی نبود، به مقاومت برو

    elif signal == "SELL":
        entry = last_close
        sl = max(recent_resistance, high[-3:].max()) * 1.002  # کمی بالای مقاومت
        fib = calculate_fib_levels(recent_resistance, recent_support)
        tp = fib['0.618']  # ولی از بالا به پایین (فروش)
        if tp >= entry:
            tp = fib['0.0']  # به پشتیبانی

    else:
        return None, None, None

    return round(entry, 4), round(sl, 4), round(tp, 4)
