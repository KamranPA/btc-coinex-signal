# config.py
import os

# تنظیمات عمومی
SYMBOL = "BTC/USDT"
TIMEFRAME = "15m"
EXCHANGE = "binance"

# خواندن توکن و شناسه از محیط (از GitHub Secrets)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# بررسی امنیتی — فقط هشدار، نه خطا
if not TELEGRAM_TOKEN:
    print("⚠️  هشدار: TELEGRAM_TOKEN تنظیم نشده. اگر این یک تست است، ادامه دهید.")
if not CHAT_ID:
    print("⚠️  هشدار: CHAT_ID تنظیم نشده.")

# (اختیاری) برای تست محلی، می‌توانید این خطوط را فعال کنید:
# TELEGRAM_TOKEN = "7845123690:AAFdjkfjdnJNJKFNSKJFNSJFNSJFNSJFNSJF"  # ← فقط برای تست محلی
# CHAT_ID = "123456789"
