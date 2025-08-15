# data_handler.py
import ccxt
import pandas as pd
from datetime import datetime, timedelta

def fetch_binance_data(symbol, timeframe, limit=100, start_date=None):
    exchange = ccxt.binance({
        'options': {
            'adjustForTimezone': False
        }
    })

    # دریافت داده‌ها
    ohlcv = exchange.fetch_ohlcv(
        symbol=symbol,
        timeframe=timeframe,
        limit=limit
    )

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df
