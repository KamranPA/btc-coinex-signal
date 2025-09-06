import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.coinex_api import CoinExAPI
from unittest.mock import patch, Mock

class TestCoinExAPI:
    
    @pytest.fixture
    def coinex_api(self):
        return CoinExAPI()
    
    def test_generate_signature(self, coinex_api):
        """تست تولید signature"""
        params = {'market': 'BTCUSDT', 'type': '15min'}
        signature = coinex_api._generate_signature(params)
        
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hash length
    
    @patch('services.coinex_api.requests.get')
    def test_get_market_data_success(self, mock_get, coinex_api):
        """تست دریافت داده بازار با موفقیت"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'data': [
                [1609459200, '29000', '29100', '28900', '29050', '1000'],
                [1609459260, '29050', '29150', '29000', '29100', '1200']
            ]
        }
        mock_get.return_value = mock_response
        
        data = coinex_api.get_market_data('BTCUSDT', 'kline', 2, '15min')
        
        assert data is not None
        assert len(data) == 2
        assert data[0][4] == '29050'  # Close price
    
    @patch('services.coinex_api.requests.get')
    def test_get_market_data_failure(self, mock_get, coinex_api):
        """تست شکست در دریافت داده بازار"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        data = coinex_api.get_market_data('BTCUSDT', 'kline', 2, '15min')
        
        assert data is None
    
    @patch('services.coinex_api.requests.get')
    def test_get_current_price(self, mock_get, coinex_api):
        """تست دریافت قیمت فعلی"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'code': 0,
            'data': {
                'ticker': {
                    'last': '29500.50'
                }
            }
        }
        mock_get.return_value = mock_response
        
        price = coinex_api.get_current_price('BTCUSDT')
        
        assert price == 29500.50

if __name__ == "__main__":
