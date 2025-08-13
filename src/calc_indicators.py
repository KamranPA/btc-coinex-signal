import pandas as pd
import json

def add_indicators(df):
    with open('config/settings.json') as f:
        config = json.load(f)
    i = config['indicators']

    # EMA
    df['ema20'] = df['close'].ewm(span=i['ema_fast']).mean()
    df['ema50'] = df['close'].ewm(span=i['ema_slow']).mean()

    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(i['rsi_period']).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(i['rsi_period']).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # ATR
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(i['atr_period']).mean()

    return df
