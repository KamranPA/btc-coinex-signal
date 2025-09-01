# main.py
import requests
import os
from datetime import datetime, timedelta
import time

# ———————————————————————
# تنظیمات از متغیرهای محیطی (GitHub Secrets & Inputs)
# ———————————————————————
TARGET_DATE = os.getenv("TARGET_DATE")  # فرمت: YYYY-MM-DD
TARGET_HOUR = int(os.getenv("TARGET_HOUR"))  # 0 تا 23
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ———————————————————————
# API CoinEx
# ———————————————————————
COINEX_API = "https://api.coinex.com/v1/market/kline"
MARKET = "BTCUSDT"
INTERVAL = "60"  # 1H

def timestamp_to_utc(dt):
    return int(time.mktime(dt.timetuple()))

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"❌ ارسال تلگرام شکست خورد: {e}")

def fetch_candles(start_time, end_time):
    params = {
        "market": MARKET,
        "interval": INTERVAL,
        "start_at": start_time,
        "end_at": end_time,
        "limit": 100
    }
    try:
        response = requests.get(COINEX_API, params=params, timeout=10)
        data = response.json()
        if data["code"] == 0:
            return data["data"]
        else:
            send_telegram(f"❌ خطای API CoinEx: {data['message']}")
            return None
    except Exception as e:
        send_telegram(f"❌ خطا در ارتباط با CoinEx: {e}")
        return None

def analyze_candle(candle):
    o, c, h, l, v = float(candle[1]), float(candle[2]), float(candle[3]), float(candle[4]), float(candle[5])
    body = abs(c - o)
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    range_ = h - l
    body_pct = body / range_ if range_ > 0 else 0
    volume = v

    analysis = f"*تحلیل کندل {candle[0]}*\n"
    analysis += f"📌 زمان: `{datetime.utcfromtimestamp(candle[0]).strftime('%Y-%m-%d %H:%M')} UTC`\n"
    analysis += f"📊 قیمت‌ها: O={o:.2f} | H={h:.2f} | L={l:.2f} | C={c:.2f}\n"
    analysis += f"🟢 وضعیت: {'سبز' if c > o else 'قرمز'}\n"
    analysis += f"📏 بدنه: {body_pct:.1%} از کندل\n"
    analysis += f"🪙 حجم: {volume:.3f} BTC\n"

    # تشخیص الگو
    if body_pct > 0.8:
        analysis += "🔖 الگو: مارابوزو (قدرتمند)\n"
    elif body_pct < 0.3:
        if upper_wick > 2 * body and lower_wick < body:
            analysis += "🔖 الگو: چکش معکوس (نگرانی فروش)\n"
        elif lower_wick > 2 * body and upper_wick < body:
            analysis += "🔖 الگو: چکش (نگرانی خرید)\n"
        else:
            analysis += "🔖 الگو: دوجی/چرک (بی‌ثباتی)\n"
    else:
        analysis += "🔖 الگو: عادی\n"

    return analysis

def main():
    try:
        # تبدیل ورودی به datetime
        target_dt = datetime.strptime(TARGET_DATE, "%Y-%m-%d")
        target_dt = target_dt.replace(hour=TARGET_HOUR, minute=0, second=0, microsecond=0)
        start_time = timestamp_to_utc(target_dt)
        end_time = start_time + 3600  # فقط یک کندل

        print(f"دریافت کندل برای: {target_dt} UTC")

        candles = fetch_candles(start_time, end_time)
        if not candles:
            send_telegram("❌ داده‌ای دریافت نشد.")
            return

        target_candle = None
        for candle in candles:
            ts = int(candle[0])
            if start_time <= ts < end_time:
                target_candle = candle
                break

        if target_candle:
            analysis = analyze_candle(target_candle)
            send_telegram(analysis)
        else:
            send_telegram(f"❌ کندل مربوط به {target_dt} یافت نشد.")
    except Exception as e:
        send_telegram(f"❌ خطای داخلی: {e}")
        print(e)

if __name__ == "__main__":
    main()
