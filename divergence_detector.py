# divergence_detector.py
import numpy as np
import pandas as pd

def calculate_rsi(series, length=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def find_pivot_low(series, left=5, right=5):
    pivot = np.full(len(series), False)
    for i in range(left, len(series) - right):
        if all(series[i] < series[i - j] for j in range(1, left + 1)) and \
           all(series[i] < series[i + j] for j in range(1, right + 1)):
            pivot[i] = True
    return pivot

def find_pivot_high(series, left=5, right=5):
    pivot = np.full(len(series), False)
    for i in range(left, len(series) - right):
        if all(series[i] > series[i - j] for j in range(1, left + 1)) and \
           all(series[i] > series[i + j] for j in range(1, right + 1)):
            pivot[i] = True
    return pivot

class DivergenceDetector:
    def __init__(self, df, rsi_length=14):
        self.df = df.copy()
        self.rsi_length = rsi_length
        self.prepare_data()

    def prepare_data(self):
        # محاسبه مومنتوم (مانند کد Pine)
        self.df['momentum'] = self.df['close'].diff(10)
        self.df['rsi'] = calculate_rsi(self.df['momentum'], self.rsi_length)

    def detect(self):
        df = self.df
        left, right = 5, 5

        # پیدا کردن پیوت‌ها
        df['pl'] = find_pivot_low(df['low'], left, right)
        df['ph'] = find_pivot_high(df['high'], left, right)

        signals = []

        # بررسی واگرایی صعودی (قیمت پایین‌تر، RSI بالاتر)
        for i in range(right, len(df)):
            if df['pl'].iloc[i]:
                for j in range(i - 1, i - 20, -1):
                    if df['pl'].iloc[j] and j >= 0:
                        price_ll = df['low'].iloc[i] < df['low'].iloc[j]
                        rsi_hl = df['rsi'].iloc[i] > df['rsi'].iloc[j]
                        if price_ll and rsi_hl:
                            signals.append({
                                'type': 'Bullish',
                                'direction': 'With Trend' if df['close'].iloc[i] > df['close'].iloc[i-50] else 'Counter-Trend',
                                'timestamp': df.index[i],
                                'price': df['low'].iloc[i],
                                'rsi': df['rsi'].iloc[i]
                            })
                        break

            if df['ph'].iloc[i]:
                for j in range(i - 1, i - 20, -1):
                    if df['ph'].iloc[j] and j >= 0:
                        price_hh = df['high'].iloc[i] > df['high'].iloc[j]
                        rsi_lh = df['rsi'].iloc[i] < df['rsi'].iloc[j]
                        if price_hh and rsi_lh:
                            signals.append({
                                'type': 'Bearish',
                                'direction': 'With Trend' if df['close'].iloc[i] < df['close'].iloc[i-50] else 'Counter-Trend',
                                'timestamp': df.index[i],
                                'price': df['high'].iloc[i],
                                'rsi': df['rsi'].iloc[i]
                            })
                        break

        return signals
