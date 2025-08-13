# backtest_diagnostic.py
import datetime
import pandas as pd
import ccxt
import requests

# -------------------------------
# تنظیمات
# -------------------------------
START_DATE = '2025-04-01'
END_DATE = '2025-07-01'
SYMBOL = 'BTC/USDT'
TIMEFRAME = '15m'

# توکن تلگرام — خودتان وارد کنید
TELEGRAM_TOKEN = "7123456789:AAHd123abcDEFgh456ijk789LMNOPqrstuv"
TELEGRAM_CHAT_ID = "123456789"

# -------------------------------
# 1. دریافت داده
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
        except: break

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
# 🔍 فیلتر ۱: ساختار بازار
# -------------------------------
def check_structure(df):
    l = df.iloc[-1]
    p = df.iloc[-2]
    pp = df.iloc[-3]
    long = (p['low'] > pp['low']) and (l['high'] > p['high'])
    short = (p['high'] < pp['high']) and (l['low'] < p['low'])
    return {"long": long, "short": short}

# -------------------------------
# 🔍 فیلتر ۲: شکست ساختار (BOS)
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
# 🔍 فیلتر ۳: جریان نقدینگی
# -------------------------------
def detect_liquidity_grab(df):
    l = df.iloc[-1]
    p = df.iloc[-2]
    body_ratio = abs(p['open'] - p['close']) / (p['high'] - p['low']) if p['high'] != p['low'] else 0
    is_doji = body_ratio < 0.3
    strong_candle = (l['close'] > l['open'] and l['close'] == l['high']) or \
                    (l['close'] < l['open'] and l['close'] == l['low'])
    volume_ok = l['volume'] > df['volume'].tail(10).mean() * 1.5

    return {
        "long": is_doji and strong_candle and l['close'] > p['high'] and volume_ok,
        "short": is_doji and strong_candle and l['close'] < p['low'] and volume_ok
    }

# -------------------------------
# 🔍 فیلتر ۴: واگرایی RSI
# -------------------------------
def detect_divergence(df):
    if len(df) < 5: return {"long": False, "short": False}
    low, high, rsi = df['low'].tail(5), df['high'].tail(5), df['rsi'].tail(5)
    return {
        "long": low.is_monotonic_decreasing and not rsi.is_monotonic_decreasing,
        "short": high.is_monotonic_increasing and not rsi.is_monotonic_increasing
    }

# -------------------------------
# 4. اجرای تشخیصی (فیلتر به فیلتر)
# -------------------------------
def run_diagnostic(df):
    results = []

    for i in range(10, len(df)):
        temp_df = df.iloc[:i+1].copy()
        temp_df = add_rsi(temp_df)
        l = temp_df.iloc[-1]

        # فراخوانی هر فیلتر
        s = check_structure(temp_df)
        b = detect_bos(temp_df)
        lq = detect_liquidity_grab(temp_df)
        d = detect_divergence(temp_df)

        # ذخیره نتیجه
        results.append({
            "time": l['timestamp'],
            "price": l['close'],
            "structure_long": s['long'],
            "structure_short": s['short'],
            "bos_long": b['long'],
            "bos_short": b['short'],
            "liquidity_long": lq['long'],
            "liquidity_short": lq['short'],
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

    report = "🔍 <b>گزارش تشخیصی فیلترها</b>\n"
    report += f"📅 دوره: {START_DATE} تا {END_DATE}\n"
    report += f"📌 جفت: {SYMBOL} | ⏱ تایم‌فریم: {TIMEFRAME}\n\n"

    for name in ['structure', 'bos', 'liquidity', 'divergence']:
        long_count = diag_df[f"{name}_long"].sum()
        short_count = diag_df[f"{name}_short"].sum()
        report += f"🔹 <b>{name.upper()}</b>\n"
        report += f"  ✅ لانگ: {long_count}\n"
        report += f"  🔻 شورت: {short_count}\n\n"

    # تحلیل ترکیبی
    all_long = ((diag_df['structure_long'] & diag_df['bos_long'] &
                 diag_df['liquidity_long'] & diag_df['divergence_long']).sum())
    all_short = ((diag_df['structure_short'] & diag_df['bos_short'] &
                  diag_df['liquidity_short'] & diag_df['divergence_short']).sum())

    report += "🎯 <b>ترکیب کامل (همه ۴ فیلتر)</b>\n"
    report += f"  ✅ لانگ: {all_long}\n"
    report += f"  🔻 شورت: {all_short}\n"
    report += "\n#تشخیص #فیلتر #نهادی"

    return report

# -------------------------------
# 6. ارسال به تلگرام
# -------------------------------
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.post(url, data=data, timeout=10)
    except: pass

# -------------------------------
# 7. اجرای اصلی
# -------------------------------
def main():
    print("🔍 شروع تحلیل تشخیصی فیلترها...")
    df = fetch_data()
    if len(df) < 10:
        msg = "❌ داده کافی دریافت نشد"
        print(msg)
        send_telegram(msg)
        return

    diag_df = run_diagnostic(df)
    report = generate_diagnostic_report(diag_df)
    print(report)
    send_telegram(report)

if __name__ == "__main__":
    main()
