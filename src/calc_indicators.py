import pandas as pd
import json

def add_all_indicators(df):
    df = df.copy()
    with open('config/settings.json') as f:
        config = json.load(f)
    i = config['indicators']

    df['ema20'] = df['close'].ewm(span=i['ema_fast']).mean()
    df['ema50'] = df['close'].ewm(span=i['ema_slow']).mean()
    df['ema200'] = df['close'].ewm(span=i['ema_trend']).mean()

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(i['rsi_period']).mean()
    loss = -delta.where(delta < 0, 0).rolling(i['rsi_period']).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    df['high_low'] = df['high'] - df['low']
    df['high_close'] = abs(df['high'] - df['close'].shift())
    df['low_close'] = abs(df['low'] - df['close'].shift())
    tr = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    df['atr'] = tr.rolling(i['atr_period']).mean()

    return df
