import ccxt
import pandas as pd
import json

def fetch_data():
    with open('config/settings.json') as f:
        config = json.load(f)
    
    exchange = ccxt.kucoin({
        'enableRateLimit': True,
        'rateLimit': 2000
    })
    
    ohlcv = exchange.fetch_ohlcv(
        config['symbol'], 
        config['timeframe'], 
        limit=config['limit']
    )
    
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df
