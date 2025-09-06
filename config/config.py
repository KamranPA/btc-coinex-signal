import os
from dotenv import load_dotenv

load_dotenv()

# تنظیمات CoinEx
COINEX_ACCESS_ID = os.getenv('COINEX_ACCESS_ID', '')
COINEX_SECRET_KEY = os.getenv('COINEX_SECRET_KEY', '')
COINEX_BASE_URL = 'https://api.coinex.com/v1'

# تنظیمات تلگرام
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# تنظیمات استراتژی
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
TIMEFRAME = '15min'
SENSITIVITY = 2.4
SIGNAL_TUNER = 10

# تنظیمات ریسک
RISK_REWARD_RATIOS = {
    'TP1': 1.0,
    'TP2': 2.0,
    'TP3': 3.0
}
STOP_LOSS_MULTIPLIER = 2.2
