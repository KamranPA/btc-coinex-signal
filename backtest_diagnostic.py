# backtest_diagnostic.py
import datetime
import pandas as pd
import ccxt
import requests

# -------------------------------
# تنظیمات
# -------------------------------
START_DATE = '2025-01-04'
END_DATE = '2025-05-01'
SYMBOL = 'BTC/USDT'
TIMEFRAME = '15m'

# اطلاعات ربات تلگرام — توکن و چت آیدی را وارد کنید
TELEGRAM_TOKEN = "7123456789:AAHd123abcDEFgh456ijk789LMNOPqrstuv"  # ← عوض کنید
TELEGRAM_CHAT_ID = "123456789"  # ← عوض کنید

# -------------------------------
# 1. دریافت داده از KuCoin
# -------------------------------
def fetch_data():
    exchange = ccxt.kucoin({'enableRateLimit': True, 'rateLimit': 2000})
    since = exchange.parse8601(f"{START_DATE}T00:00:00Z")
    end = exchange.parse8601(f"{END_DATE}T00:00:00Z")
    all_ohlcv = []

    while since < end:
        try:
            ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, since, limit=500)
            if not ohlcv: break
            since = ohlcv[-1][0] + 1
            all_ohlcv.extend(ohlcv)
        except Exception as e:
            print(f"❌ خطا در دریافت داده: {str(e)}")
            break

    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    if df.empty: return df
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[(df['timestamp'] >= START_DATE) & (df['timestamp'] < END_DATE)]
    return df

# -------------------------------
# 2. محاسبه RSI
# -------------------------------
def add_rsi(df, period=14):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

# -------------------------------
# 🔍 فیلتر ۱: ساختار بازار (Market Structure)
# -------------------------------
def check_structure(df):
    l = df.iloc[-1]
    p = df.iloc[-2]
    pp = df.iloc[-3]

    long = (p['low'] > pp['low']) and (l['high'] > p['high'])
    short = (p['high'] < pp['high']) and (l['low'] < p['low'])

    return {"long": long, "short": short}

# -------------------------------
# 🔍 فیلتر ۲: شکست ساختار (Break of Structure - BOS)
# -------------------------------
def detect_bos(df):
    l = df.iloc[-1]
    recent_high = df['high'].rolling(5).max().iloc[-2]
    recent_low = df['low'].rolling(5).min().iloc[-2]

    return {
        "long": l['close'] > recent_high,
        "short": l['close'] < recent_low
    }

# -------------------------------
# 🔍 فیلتر ۳: واگرایی RSI
# -------------------------------
def detect_divergence(df):
    if len(df) < 5:
        return {"long": False, "short": False}

    # آخرین 5 کندل
    low = df['low'].tail(5)
    high = df['high'].tail(5)
    rsi = df['rsi'].tail(5)

    # واگرایی صعودی (Long): قیمت کف جدید، RSI کف جدید نه
    long = low.is_monotonic_decreasing and not rsi.is_monotonic_decreasing

    # واگرایی نزولی (Short): قیمت سقف جدید، RSI سقف جدید نه
    short = high.is_monotonic_increasing and not rsi.is_monotonic_increasing

    return {"long": long, "short": short}

# -------------------------------
# 4. اجرای تشخیصی (فیلتر به فیلتر)
# -------------------------------
def run_diagnostic(df):
    results = []

    for i in range(10, len(df)):
        temp_df = df.iloc[:i+1].copy()
        temp_df = add_rsi(temp_df)
        l = temp_df.iloc[-1]

        # اعمال هر فیلتر
        s = check_structure(temp_df)
        b = detect_bos(temp_df)
        d = detect_divergence(temp_df)

        # ذخیره نتایج
        results.append({
            "time": l['timestamp'],
            "price": l['close'],
            "structure_long": s['long'],
            "structure_short": s['short'],
            "bos_long": b['long'],
            "bos_short": b['short'],
            "divergence_long": d['long'],
            "divergence_short": d['short']
        })

    return pd.DataFrame(results)

# -------------------------------
# 5. گزارش تشخیصی
# -------------------------------
def generate_diagnostic_report(diag_df):
    total = len(diag_df)
    if total == 0:
        return "❌ داده کافی برای تحلیل وجود ندارد."

    report = "🔍 <b>گزارش تشخیصی فیلترها (بدون liquidity)</b>\n"
    report += f"📅 دوره: {START_DATE} تا {END_DATE}\n"
    report += f"📌 جفت: {SYMBOL} | ⏱ تایم‌فریم: {TIMEFRAME}\n\n"

    for name in ['structure', 'bos', 'divergence']:
        long_count = diag_df[f"{name}_long"].sum()
        short_count = diag_df[f"{name}_short"].sum()
        report += f"🔹 <b>{name.upper()}</b>\n"
        report += f"  ✅ لانگ: {long_count}\n"
        report += f"  🔻 شورت: {short_count}\n\n"

    # تحلیل ترکیبی: هر ۳ فیلتر هم‌زمان
    all_long = (
        (diag_df['structure_long'] & 
         diag_df['bos_long'] & 
         diag_df['divergence_long'])
    ).sum()

    all_short = (
        (diag_df['structure_short'] & 
         diag_df['bos_short'] & 
         diag_df['divergence_short'])
    ).sum()

    report += "🎯 <b>ترکیب کامل (ساختار + BOS + واگرایی)</b>\n"
    report += f"  ✅ لانگ: {all_long}\n"
    report += f"  🔻 شورت: {all_short}\n"

    if all_long > 0 or all_short > 0:
        report += f"\n✅ {all_long + all_short} سیگنال نهادی شناسایی شد."
    else:
        report += "\n🟡 هیچ سیگنالی با ترکیب کامل تولید نشد."

    report += "\n\n#تشخیص #نهادی #بدون_نقدینگی"

    return report

# -------------------------------
# 6. ارسال به تلگرام
# -------------------------------
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, data=data, timeout=10)
        print("✅ گزارش به تلگرام ارسال شد")
    except Exception as e:
        print(f"❌ ارسال ناموفق: {str(e)}")

# -------------------------------
# 7. اجرای اصلی
# -------------------------------
def main():
    print(f"🔍 شروع تحلیل تشخیصی (بدون liquidity): {START_DATE} تا {END_DATE}")
    df = fetch_data()
    
    if df is None or len(df) < 10:
        error_msg = f"❌ بک‌تست ناموفق: داده کافی دریافت نشد ({len(df)} کندل)"
        print(error_msg)
        send_telegram(error_msg)
        return

    diag_df = run_diagnostic(df)
    report = generate_diagnostic_report(diag_df)
    print(report)
    send_telegram(report)

if __name__ == "__main__":
    main()
