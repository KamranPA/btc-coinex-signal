# backtest.py
import datetime
import pandas as pd
import ccxt
import requests

# -------------------------------
# تنظیمات بک‌تست
# -------------------------------
START_DATE = '2025-04-01'      # ← می‌توانید بعداً تغییر دهید
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
        except: break

    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    if df.empty: return df
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[(df['timestamp'] >= START_DATE) & (df['timestamp'] < END_DATE)]
    return df

# -------------------------------
# 2. محاسبه RSI (فقط برای واگرایی)
# -------------------------------
def add_rsi(df, period=14):
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

# -------------------------------
# 3. فیلتر ۱: ساختار بازار
# -------------------------------
def check_structure(df):
    l, p, pp = df.iloc[-1], df.iloc[-2], df.iloc[-3]
    long = (p['low'] > pp['low']) and (l['high'] > p['high'])
    short = (p['high'] < pp['high']) and (l['low'] < p['low'])
    return {"long": long, "short": short}

# -------------------------------
# 4. فیلتر ۲: شکست ساختار (BOS)
# -------------------------------
def detect_bos(df):
    l = df.iloc[-1]
    recent_high = df['high'].rolling(5).max().iloc[-2]
    recent_low = df['low'].rolling(5).min().iloc[-2]
    long = l['close'] > recent_high
    short = l['close'] < recent_low
    return {"long": long, "short": short}

# -------------------------------
# 5. فیلتر ۳: واگرایی RSI
# -------------------------------
def detect_divergence(df):
    if len(df) < 5: return {"long": False, "short": False}
    low, high, rsi = df['low'].tail(5), df['high'].tail(5), df['rsi'].tail(5)
    long = low.is_monotonic_decreasing and not rsi.is_monotonic_decreasing
    short = high.is_monotonic_increasing and not rsi.is_monotonic_increasing
    return {"long": long, "short": short}

# -------------------------------
# 6. فیلتر ۴: جریان نقدینگی
# -------------------------------
def detect_liquidity_grab(df):
    l, p = df.iloc[-1], df.iloc[-2]
    body_ratio = abs(p['open'] - p['close']) / (p['high'] - p['low']) if p['high'] != p['low'] else 0
    is_doji = body_ratio < 0.3
    strong_candle = (l['close'] > l['open'] and l['close'] == l['high']) or \
                    (l['close'] < l['open'] and l['close'] == l['low'])
    long = is_doji and strong_candle and l['close'] > p['high']
    short = is_doji and strong_candle and l['close'] < p['low']
    return {"long": long, "short": short}

# -------------------------------
# 7. شبیه‌سازی معاملات
# -------------------------------
def run_backtest(df):
    trades = []
    in_trade = False
    entry, sl, tp, side = 0, 0, 0, None

    for i in range(5, len(df)):
        temp_df = df.iloc[:i+1].copy()
        temp_df = add_rsi(temp_df)

        s = check_structure(temp_df)
        b = detect_bos(temp_df)
        d = detect_divergence(temp_df)
        l = detect_liquidity_grab(temp_df)

        if not in_trade:
            if all([s['long'], b['long'], d['long'], l['long']]):
                entry = temp_df.iloc[-1]['close']
                atr = temp_df['high'].iloc[-5:].max() - temp_df['low'].iloc[-5:].min()
                sl = entry - 1.5 * atr
                tp = entry + 2 * (entry - sl)
                side = "long"
                in_trade = True
            elif all([s['short'], b['short'], d['short'], l['short']]):
                entry = temp_df.iloc[-1]['close']
                atr = temp_df['high'].iloc[-5:].max() - temp_df['low'].iloc[-5:].min()
                sl = entry + 1.5 * atr
                tp = entry - 2 * (sl - entry)
                side = "short"
                in_trade = True
        else:
            low, high = temp_df.iloc[-1]['low'], temp_df.iloc[-1]['high']
            if side == "long" and (low <= sl or high >= tp):
                trades.append({"type": "win" if high >= tp else "loss", "side": "long"})
                in_trade = False
            elif side == "short" and (high >= sl or low <= tp):
                trades.append({"type": "win" if low <= tp else "loss", "side": "short"})
                in_trade = False

    return trades

# -------------------------------
# 8. گزارش و ارسال به تلگرام
# -------------------------------
def generate_report(trades):
    if not trades:
        return f"📊 بک‌تست: هیچ سیگنالی در <b>{START_DATE}</b> تا <b>{END_DATE}</b> تولید نشد."

    wins = [t for t in trades if t['type'] == 'win']
    win_rate = len(wins) / len(trades) * 100

    return f"""
🎯 <b>گزارش بک‌تست بر پایه منطق نهادی</b>
📅 دوره: {START_DATE} تا {END_DATE}
📌 جفت: {SYMBOL}
⏱ تایم‌فریم: {TIMEFRAME}

🔢 معاملات: {len(trades)}
✅ سودآور: {len(wins)}
❌ ضررده: {len(trades)-len(wins)}
📊 نرخ موفقیت: {win_rate:.1f}%

💡 فیلترها: ساختار + BOS + واگرایی + نقدینگی
#بکتست #نهادی #اصولی
"""

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.post(url, data=data, timeout=10)
    except: pass

# -------------------------------
# 9. اجرای اصلی
# -------------------------------
def main():
    df = fetch_data()
    if len(df) < 10:
        msg = "❌ بک‌تست ناموفق: داده کافی دریافت نشد"
        print(msg)
        send_telegram(msg)
        return

    df = add_rsi(df)
    trades = run_backtest(df)
    report = generate_report(trades)
    print(report)
    send_telegram(report)

if __name__ == "__main__":
    main()
