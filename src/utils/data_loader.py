# src/utils/data_loader.py
import requests
import pandas as pd
from datetime import datetime

def load_data_from_coinex(symbol="BTC-USDT", timeframe="1h", limit=1000):
    """
    Load real OHLCV data from CoinEx API
    """
    # تنظیم endpoint و پارامترها
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

        # استخراج داده‌ها
        klines = data['data']
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'close', 'high', 'low', 'volume', 'amount'])
        
        # تبدیل timestamp به datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)
        
        # تبدیل ستون‌ها به float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)

        print(f"✅ Loaded {len(df)} candles from CoinEx for {symbol} on {timeframe}")
        return df

    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        return None
