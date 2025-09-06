import requests
import hashlib
import hmac
import time
import json
from urllib.parse import urlencode
from config.config import COINEX_ACCESS_ID, COINEX_SECRET_KEY, COINEX_BASE_URL

class CoinExAPI:
    def __init__(self):
        self.access_id = COINEX_ACCESS_ID
        self.secret_key = COINEX_SECRET_KEY
        self.base_url = COINEX_BASE_URL
        
    def _generate_signature(self, params):
        params_sorted = sorted(params.items())
        query_string = urlencode(params_sorted)
        signature = hmac.new(
            self.secret_key.encode(), 
            query_string.encode(), 
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def get_market_data(self, symbol, type='kline', limit=100, timeframe='15min'):
        endpoint = '/market/kline'
        params = {
            'market': symbol,
            'type': timeframe,
            'limit': limit
        }
        
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 0:
                return data['data']
        return None
    
    def get_current_price(self, symbol):
        endpoint = '/market/ticker'
        params = {'market': symbol}
        
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 0:
                return float(data['data']['ticker']['last'])
        return None
