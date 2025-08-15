# config.py
import os

SYMBOL = "BTC/USDT"
TIMEFRAME = "15m"
EXCHANGE = "binance"

# خواندن از متغیرهای محیطی (که از Secrets می‌آیند)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
