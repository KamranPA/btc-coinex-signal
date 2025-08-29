import numpy as np
import pandas as pd

def detect_rsi_momentum_divergence(df, rsi_length=14, lookback=5):
    """
    تشخیص واگرایی صعودی/نزولی بر اساس RSI روی مومنتوم قیمت
    """
    # محاسبه مومنتوم و RSI
    df['momentum'] = df['close'].diff(10)
    df['rsi'] = ta.momentum.RSIIndicator(df['momentum'], window=rsi_length).rsi()

    # پیوت‌های قیمت و RSI
    df['price_low'] = df['low'].rolling(lookback*2+1, center=True).apply(lambda x: x[lookback] == x.min(), raw=True)
    df['price_high'] = df['high'].rolling(lookback*2+1, center=True).apply(lambda x: x[lookback] == x.max(), raw=True)
    df['rsi_low'] = df['rsi'].rolling(lookback*2+1, center=True).apply(lambda x: x[lookback] == x.min(), raw=True)
    df['rsi_high'] = df['rsi'].rolling(lookback*2+1, center=True).apply(lambda x: x[lookback] == x.max(), raw=True)

    # واگرایی صعودی: قیمت کف پایین‌تر، RSI کف بالاتر
    bullish = []
    for i in range(1, len(df)):
        if df['price_low'].iloc[i] and df['rsi_low'].iloc[i]:
            if df['low'].iloc[i] < df['low'].iloc[i-1] and df['rsi'].iloc[i] > df['rsi'].iloc[i-1]:
                bullish.append(i)

    # واگرایی نزولی: قیمت سقف بالاتر، RSI سقف پایین‌تر
    bearish = []
    for i in range(1, len(df)):
        if df['price_high'].iloc[i] and df['rsi_high'].iloc[i]:
            if df['high'].iloc[i] > df['high'].iloc[i-1] and df['rsi'].iloc[i] < df['rsi'].iloc[i-1]:
                bearish.append(i)

    return bullish, bearish
