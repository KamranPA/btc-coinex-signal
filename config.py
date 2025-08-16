# config.py
import os

SYMBOL = "BTC-USDT"          # فرمت صحیح KuCoin
TIMEFRAME = "1h"
EXCHANGE = "kucoin"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
