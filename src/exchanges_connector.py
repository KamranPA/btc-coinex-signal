# src/exchange_connector.py
import pandas as pd
import requests
import time
import config

class ExchangeConnector:
    def __init__(self):
        self.exchange_priority = config.EXCHANGES
        self.connected_exchange = None

    def connect(self):
        for exchange in self.exchange_priority:
            try:
                if exchange == "kucoin":
                    response = requests.get("https://api.kucoin.com/api/v1/market/allTickers", timeout=10)
                    if response.status_code == 200:
                        self.connected_exchange = "kucoin"
                        return

                elif exchange == "binance":
                    response = requests.get("https://api.binance.com/api/v3/ping", timeout=10)
                    if response.status_code == 200:
                        self.connected_exchange = "binance"
                        return

                elif exchange == "bybit":
                    response = requests.get("https://api.bybit.com/v2/public/time", timeout=10)
                    if response.status_code == 200:
                        self.connected_exchange = "bybit"
                        return

            except Exception as e:
                print(f"Connection to {exchange} failed: {str(e)}")
                time.sleep(1)

        raise ConnectionError("All exchanges failed to connect")

    def fetch_data(self, limit=500):
        self.connect()
        symbol = config.SYMBOL.replace('-', '')

        if self.connected_exchange == "kucoin":
            url = f"https://api.kucoin.com/api/v1/market/candles?type={config.TIMEFRAME}&symbol={symbol}&limit={limit}"
            response = requests.get(url, timeout=15)
            data = response.json()['data']
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'close', 'high', 'low', 'volume', 'turnover'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

        elif self.connected_exchange == "binance":
            interval = "15m" if config.TIMEFRAME == "15min" else "1h"
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
            response = requests.get(url, timeout=15)
            data = response.json()
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        elif self.connected_exchange == "bybit":
            interval = "15" if config.TIMEFRAME == "15min" else "60"
            url = f"https://api.bybit.com/public/linear/kline?symbol={symbol}&interval={interval}&limit={limit}"
            response = requests.get(url, timeout=15)
            data = response.json()['result']
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

        # تبدیل به عدد
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        df = df.dropna()

        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].sort_values('timestamp')
