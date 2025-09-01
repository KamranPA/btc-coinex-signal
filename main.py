# main.py - نسخه اصلاح‌شده با timestamp صحیح UTC
import requests
import os
import calendar
from datetime import datetime, timedelta
import time

# ———————————————————————
# تنظیمات از متغیرهای محیطی
# ———————————————————————
TARGET_DATE = os.getenv("TARGET_DATE")  # YYYY-MM-DD
TARGET_HOUR = int(os.getenv("TARGET_HOUR"))  # 0-23
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ———————————————————————
# API CoinEx
# ———————————————————————
COINEX_API = "https://api.coinex.com/v1/market/kline"
MARKET = "BTCUSDT"
INTERVAL = "60"  # 1H

def dt_to_timestamp(dt):
    """تبدیل datetime به timestamp با فرض UTC"""
    return calendar.timegm(dt.utctimetuple())

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code != 200:
            print(f"❌ ارسال تلگرام شکست خورد: {response.text}")
    except Exception as e:
        print(f"❌ خطا در ارسال تلگرام: {e}")

def fetch_candles(start_time, end_time):
    params = {
        "market": MARKET,
        "interval": INTERVAL,
        "start_at": start_time,
        "end_at": end_time,
        "limit": 100
    }
    print(f"در حال درخواست از API با پارامترها: {params}")  # لاگ برای دیباگ

    try:
        response = requests.get(COINEX_API, params=params, timeout=10)
        print(f"پاسخ API: {response.status_code} - {response.text}")  # دیباگ

        if response.status_code != 200:
            send_telegram(f"❌ خطای HTTP: {response.status_code}\n{response.text}")
            return None

        data = response.json()
        if data["code"] == 0:
            return data["data"]
        else:
            send_telegram(f"❌ خطای API CoinEx: {data.get('message', 'ناشناس')}")
            return None
    except Exception as e:
        send_telegram(f"❌ خطا در ارتباط با CoinEx: {e}")
        print(f"❌ خطا: {e}")
        return None

def analyze_candle(candle):
    # candle: [timestamp, open, close, high, low, volume, ...]
    o, c, h, l, v = float(candle[1]), float(candle[2]), float(candle[3]), float(candle[4]), float(candle[5])
    body = abs(c - o)
    upper_wick = h - max(o, c)
    lower_wick = min(o, c) - l
    range_ = h - l
    body_pct = body / range_ if range_ > 0 else 0
    volume = v

    dt = datetime.utcfromtimestamp(int(candle[0])).strftime('%Y-%m-%d %H:%M')

    analysis = f"*تحلیل کندل*\n"
    analysis += f"📌 زمان: `{dt} UTC`\n"
    analysis += f"📊 قیمت: O={o:.2f} | H={h:.2f} | L={l:.2f} | C={c:.2f}\n"
    analysis += f"🟢 وضعیت: {'🟢 سبز' if c > o else '🔴 قرمز'}\n"
    analysis += f"📏 بدنه: {body_pct:.1%}\n"
    analysis += f"🪙 حجم: {volume:.3f} BTC\n"

    if body_pct > 0.8:
        analysis += "🔖 الگو: مارابوزو (قدرت)\n"
    elif body_pct < 0.3:
        if upper_wick > 2 * body and lower_wick < body:
            analysis += "🔖 الگو: چکش معکوس ⚠️\n"
        elif lower_wick > 2 * body and upper_wick < body:
            analysis += "🔖 الگو: چکش ✅\n"
        else:
            analysis += "🔖 الگو: دوجی / بی‌ثباتی\n"
    else:
        analysis += "🔖 الگو: عادی\n"

    return analysis

def main():
    try:
        # تبدیل ورودی
        target_dt = datetime.strptime(TARGET_DATE, "%Y-%m-%d")
        target_dt = target_dt.replace(hour=TARGET_HOUR, minute=0, second=0, microsecond=0)

        # تبدیل صحیح به timestamp (UTC)
        start_time = dt_to_timestamp(target_dt)
        end_time = start_time + 3600  # یک ساعت بعد

        print(f"هدف: {target_dt} -> start_at={start_time}, end_at={end_time}")

        candles = fetch_candles(start_time, end_time)
        if not candles:
            send_telegram("❌ داده‌ای دریافت نشد.")
            return

        # پیدا کردن کندل دقیق
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
            send_telegram(f"❌ کندلی برای {target_dt.strftime('%Y-%m-%d %H:00')} یافت نشد.")
            print("کندل‌های دریافتی:", candles)

    except Exception as e:
        error_msg = f"❌ خطای داخلی: {e}"
        send_telegram(error_msg)
        print(error_msg)

if __name__ == "__main__":
    main()
