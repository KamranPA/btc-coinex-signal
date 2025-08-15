# config.py
import os

SYMBOL = "BTC/USDT"
TIMEFRAME = "15m"
EXCHANGE = "binance"

# خواندن از محیط (با پیش‌فرض None)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# بررسی امنیتی (با پیش‌فرض)
if not TELEGRAM_TOKEN:
    print("⚠️  هشدار: TELEGRAM_TOKEN در تنظیمات یافت نشد. اگر این یک تست است، می‌توانید ادامه دهید.")
    # اگر قصد دارید بک‌تست بدون تلگرام انجام شود، این خط را فعال کنید:
    # TELEGRAM_TOKEN = "dummy_token"  # فقط برای تست

if not CHAT_ID:
    print("⚠️  هشدار: CHAT_ID در تنظیمات یافت نشد.")

# اگر نمی‌خواهید از تلگرام استفاده کنید، این کد را فعال کنید:
# def send_telegram_message(*args, **kwargs):
#     pass  # حذف ارسال پیام
