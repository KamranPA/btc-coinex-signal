# config.py
import os

SYMBOL = "BTC/USDT"
TIMEFRAME = "15m"
EXCHANGE = "binance"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN:
    print("⚠️  هشدار: TELEGRAM_TOKEN در تنظیمات یافت نشد. اگر این یک تست است، می‌توانید ادامه دهید.")
if not CHAT_ID:
    print("⚠️  هشدار: CHAT_ID در تنظیمات یافت نشد.")
