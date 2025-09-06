import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from services.telegram_bot import TelegramBot
from unittest.mock import patch, Mock

class TestTelegramBot:
    
    @pytest.fixture
    def telegram_bot(self):
        return TelegramBot()
    
    def test_format_signal_message(self, telegram_bot):
        """تست فرمت‌دهی پیام سیگنال"""
        message = telegram_bot.format_signal_message(
            symbol='BTCUSDT',
            signal_type='خرید',
            entry=29000.50,
            sl=28500.00,
            tp1=29500.00,
            tp2=30000.00,
            tp3=30500.00
        )
        
        assert 'BTCUSDT' in message
        assert 'خرید' in message
        assert '29000.5' in message
        assert '28500.0' in message
        assert '29500.0' in message
    
    @patch('services.telegram_bot.requests.post')
    def test_send_message_success(self, mock_post, telegram_bot):
        """تست ارسال موفق پیام"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = telegram_bot.send_message("Test message")
        
        assert result is True
    
    @patch('services.telegram_bot.requests.post')
    def test_send_message_failure(self, mock_post, telegram_bot):
        """تست شکست در ارسال پیام"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        result = telegram_bot.send_message("Test message")
        
        assert result is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
