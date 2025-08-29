import pandas as pd
import requests
import json
from datetime import datetime

def load_data_from_coinex(symbol="BTC-USDT", timeframe="1h", limit=1000):
    """
    Load OHLCV data from CoinEx API
    """
    url = "https://api.coinex.com/v1/market/kline"
    params = {
        'market': symbol.replace('-', ''),
        'type': timeframe,
        'limit': limit
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data['code'] != 0:
            raise Exception(f"API Error: {data['message']}")

        klines = data['data']
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'close', 'high', 'low', 'volume', 'amount'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)
        df = df.astype(float)
        return df
    except Exception as e:
        from src.utils.logger import setup_logger
        logger = setup_logger()
        logger.error(f"Data fetch failed: {e}")
        return None
