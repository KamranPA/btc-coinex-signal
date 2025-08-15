# config.py
import os

SYMBOL = "BTC/USDT"          # قابل پشتیبانی توسط KuCoin
TIMEFRAME = "15m"
EXCHANGE = "kucoin"          # تغییر از binance به kucoin

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN:
    print("⚠️  هشدار: TELEGRAM_TOKEN در تنظیمات یافت نشد.")
if not CHAT_ID:
    print("⚠️  هشدار: CHAT_ID در تنظیمات یافت نشد.")
