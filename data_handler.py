# data_handler.py
import ccxt
import pandas as pd
from datetime import datetime, timedelta

def fetch_binance_data(symbol, timeframe, limit=100, start_date=None, end_date=None):
    exchange = ccxt.binance({
        'options': {
            'adjustForTimezone': False
        }
    })

    # تبدیل تاریخ به میلی‌ثانیه
    def to_timestamp(date_str):
        return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)

    # تنظیم پارامترها
    params = {
        'limit': limit,
        'since': to_timestamp(start_date) if start_date else None
    }

    # دریافت داده‌ها
    ohlcv = exchange.fetch_ohlcv(
        symbol=symbol,
        timeframe=timeframe,
        **params
    )

    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df
