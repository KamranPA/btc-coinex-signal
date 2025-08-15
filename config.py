# config.py
import os

# تنظیمات عمومی
SYMBOL = "BTC-USDT"          # فرمت صحیح برای KuCoin
TIMEFRAME = "15m"
EXCHANGE = "kucoin"

# خواندن از محیط (GitHub Secrets)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# بررسی و هشدار
if not TELEGRAM_TOKEN:
    print("⚠️  هشدار: TELEGRAM_TOKEN در تنظیمات یافت نشد.")
if not CHAT_ID:
    print("⚠️  هشدار: CHAT_ID در تنظیمات یافت نشد.")
