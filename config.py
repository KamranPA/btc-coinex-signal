# config.py
import os

SYMBOL = "BTC-USDT"
TIMEFRAME = "15m"
HIGHER_TIMEFRAME = "1h"  # برای فیلتر روند
EXCHANGE = "kucoin"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
