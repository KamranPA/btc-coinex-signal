# config.py

# تنظیمات بک‌تست
SYMBOL = "BTC/USDT"               # نماد
TIMEFRAME = "1h"                  # تایم‌فریم (1h, 4h, 15m, etc.)
START_DATE = "2024-01-01"         # تاریخ شروع
END_DATE = "2024-06-01"           # تاریخ پایان

# تنظیمات تلگرام
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN"  # توکن ربات تلگرام
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"  # می‌توانید از @userinfobot بگیرید

# تنظیمات استراتژی (مطابق Pine Script)
SENSITIVITY = 2.4
STUNER = 10
MSTUNER = 8
FILTER_STYLE = "Trending Signals [Mode]"  # یا Strong [Filter]
