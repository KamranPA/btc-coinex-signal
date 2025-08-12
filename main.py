import datetime
import json
import pandas as pd
import requests
import ccxt

# -------------------------------
# 1. تابع: دریافت داده از CoinEx
# -------------------------------
def fetch_data():
    try:
        exchange = ccxt.coinex({'enableRateLimit': True})
        ohlcv = exchange.fetch_ohlcv('BTC/USDT', '15m', limit=500)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"❌ خطا در دریافت داده: {str(e)}")
        return None

# -------------------------------
# 2. تابع: محاسبه اندیکاتورها
# -------------------------------
def add_indicators(df):
    if df is None or len(df) < 20:
        return df

    # EMA
    df['ema20'] = df['close'].ewm(span=20).mean()
    df['ema50'] = df['close'].ewm(span=50).mean()
    df['ema200'] = df['close'].ewm(span=200).mean()

    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # ATR
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()

    return df

# -------------------------------
# 3. تابع: ارزیابی فیلترها
# -------------------------------
def evaluate_filters(df):
    if df is None or len(df) < 2:
        return {}

    l = df.iloc[-1]  # آخرین کندل
    p = df.iloc[-2]  # کندل قبلی

    volume_avg = df['volume'].tail(20).mean()

    filters = {
        "trend": l['ema20'] > l['ema50'] > l['ema200'],
        "price_above_ema200": l['close'] > l['ema200'],
        "volume_spike": l['volume'] > 1.3 * volume_avg,
        "high_volatility": l['atr'] > 0.003 * l['close'],
        "rsi_ok": 30 < l['rsi'] < 70,
        "structure": l['low'] > p['low'] if l['close'] > l['open'] else False
    }

    return filters

# -------------------------------
# 4. تابع: محاسبه SL و TP
# -------------------------------
def calculate_risk(df, entry_price):
    l = df.iloc[-1]
    atr = l['atr']
    support = df['low'].rolling(10).min().iloc[-1]
    resistance = df['high'].rolling(10).max().iloc[-1]

    # حد ضرر هوشمند (حداقل فاصله امن)
    sl = min(
        entry_price - (1.5 * atr),
        support * 0.99,
        l['ema20'] * 0.985
    )

    # حد سود با نسبت 1:2
    tp = entry_price + 2 * (entry_price - sl)
    rr = (tp - entry_price) / (entry_price - sl) if entry_price > sl else 0

    return {
        "sl": round(sl, 2),
        "tp": round(tp, 2),
        "risk_reward": round(rr, 2),
        "rr_ok": rr >= 1.8
    }

# -------------------------------
# 5. تابع: ارسال سیگنال به تلگرام
# -------------------------------
def send_telegram_signal(entry, tp, sl, rr, filters):
    # ⚠️ توکن و چت آیدی را خودتان وارد کنید
    TOKEN = "8205878716:AAFOSGnsF1gnY3kww1WvPT0HYubCkyPaC64"  # ← اینجا عوض کنید
    CHAT_ID = "104506829"  # ← اینجا عوض کنید

    success_filters = sum(1 for v in filters.values() if v)
    message = (
        f"🟢 <b>سیگنال خرید BTC/USDT</b>\n"
        f"📌 ورود: {entry}\n"
        f"🎯 حد سود: {tp}\n"
        f"⛔ حد ضرر: {sl}\n"
        f"📊 نسبت ریسک به ریوارد: 1:{rr}\n"
        f"✅ فیلترهای موفق: {success_filters}/6\n"
        f"🕒 زمان: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }

    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("✅ سیگنال به تلگرام ارسال شد")
        else:
            print(f"❌ خطا در ارسال تلگرام: {response.status_code}")
    except Exception as e:
        print(f"❌ خطا در اتصال تلگرام: {str(e)}")

# -------------------------------
# 6. تابع اصلی
# -------------------------------
def main():
    print("🚀 شروع سیستم سیگنال‌دهی بیت‌کوین...")
    
    # مرحله ۱: دریافت داده
    df = fetch_data()
    if df is None or len(df) < 100:
        print("❌ داده کافی دریافت نشد")
        return

    # مرحله ۲: اندیکاتورها
    df = add_indicators(df)
    if df is None or 'rsi' not in df or pd.isna(df['rsi'].iloc[-1]):
        print("❌ محاسبه اندیکاتورها ناموفق")
        return

    # مرحله ۳: فیلترها
    filters = evaluate_filters(df)
    print("🔍 وضعیت فیلترها:")
    for name, passed in filters.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")

    # مرحله ۴: بررسی شرایط
    required_conditions = [
        filters['trend'],
        filters['price_above_ema200'],
        filters['volume_spike'],
        filters['high_volatility'],
        filters['rsi_ok'],
        filters['structure']
    ]

    if all(required_conditions):
        entry_price = df['close'].iloc[-1]
        risk_data = calculate_risk(df, entry_price)

        if risk_data['rr_ok']:
            print(f"🎯 شرایط فیلترها برقرار — ارسال سیگنال")
            send_telegram_signal(
                entry=round(entry_price, 2),
                tp=risk_data['tp'],
                sl=risk_data['sl'],
                rr=risk_data['risk_reward'],
                filters=filters
            )
        else:
            print(f"📉 نسبت ریسک به ریوارد کافی نیست: {risk_data['risk_reward']}")
    else:
        print("🟡 همه فیلترها برقرار نیستند — سیگنال صادر نشد")

# -------------------------------
# اجرای برنامه
# -------------------------------
if __name__ == "__main__":
    main()
