# config.py
import os

# تنظیمات عمومی
SYMBOL = "BTC/USDT"
TIMEFRAME = "15m"
EXCHANGE = "kucoin"

# خواندن توکن و شناسه از محیط (از GitHub Secrets)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# هشدار در صورت عدم وجود توکن یا چت آی‌دی
if not TELEGRAM_TOKEN:
    print("⚠️  هشدار: TELEGRAM_TOKEN در تنظیمات یافت نشد.")
if not CHAT_ID:
    print("⚠️  هشدار: CHAT_ID در تنظیمات یافت نشد.")
