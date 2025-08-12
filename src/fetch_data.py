import ccxt
import pandas as pd
import json

def fetch_coinex_data():
    with open('config/settings.json') as f:
        config = json.load(f)
    ex = ccxt.coinex({'enableRateLimit': True})
    ohlcv = ex.fetch_ohlcv(config['symbol'], config['timeframe'], limit=config['limit'])
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df
