# config.py
import os

SYMBOL = "BTC/USDT"
TIMEFRAME = "15m"
EXCHANGE = "binance"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# بررسی امنیتی (اختیاری اما توصیه می‌شود)
if not TELEGRAM_TOKEN:
    raise EnvironmentError("❌ TELEGRAM_TOKEN در تنظیمات یافت نشد!")
if not CHAT_ID:
    raise EnvironmentError("❌ CHAT_ID در تنظیمات یافت نشد!")
