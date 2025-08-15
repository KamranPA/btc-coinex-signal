# risk_management.py
import numpy as np

def calculate_atr(high, low, close, period=14):
    tr = np.zeros(len(high))
    for i in range(len(high)):
        if i == 0:
            tr[i] = high[i] - low[i]
        else:
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
    atr = np.zeros_like(tr)
    atr[period-1] = tr[:period].mean()
    for i in range(period, len(tr)):
        atr[i] = (atr[i-1] * (period-1) + tr[i]) / period
    return atr

def get_entry_sl_tp(signal, data, atr_period=14, risk_reward_ratio=2.0):
    close = data['close'].values
    high = data['high'].values
    low = data['low'].values

    atr = calculate_atr(high, low, close, atr_period)
    last_atr = atr[-1]

    entry = close[-1]

    if signal == "BUY":
        sl = entry - (1.5 * last_atr)
        tp = entry + (risk_reward_ratio * (entry - sl))
    elif signal == "SELL":
        sl = entry + (1.5 * last_atr)
        tp = entry - (risk_reward_ratio * (sl - entry))
    else:
        return None, None, None

    return round(entry, 4), round(sl, 4), round(tp, 4)
