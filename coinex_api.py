# coinex_api.py
import ccxt
import pandas as pd
from datetime import datetime
import config

def fetch_data():
    exchange = ccxt.coinex()
    symbol = config.SYMBOL
    timeframe = config.TIMEFRAME
    start_date = config.START_DATE
    end_date = config.END_DATE

    since = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
    if end_date:
        until = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)
    else:
        until = exchange.milliseconds()

    all_candles = []
    while since < until:
        try:
            candles = exchange.fetch_ohlcv(symbol, timeframe, since, limit=1000)
            if not candles:
                break
            all_candles += candles
            since = candles[-1][0] + 1
            if candles[-1][0] >= until:
                break
        except Exception as e:
            print(f"Error fetching  {e}")
            break

    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df
