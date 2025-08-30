# data_fetcher.py
import ccxt
import pandas as pd
from datetime import datetime

def fetch_ohlcv(symbol, timeframe, limit=500):
    """
    داده‌های کندل را از Binance می‌گیرد
    """
    exchange = ccxt.binance({
        'enableRateLimit': True,
    })
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df
