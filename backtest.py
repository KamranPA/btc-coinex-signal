# backtest.py
import datetime
import pandas as pd
import ccxt
import requests
import json

# -------------------------------
# تنظیمات
# -------------------------------
START_DATE = '2025-04-01'
END_DATE = '2025-05-01'
SYMBOL = 'BTC/USDT'
TIMEFRAME = '15m'

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
# 2. اندیکاتورها
# -------------------------------
def add_indicators(df):
    df['ema20'] = df['close'].ewm(span=20).mean()
    df['ema50'] = df['close'].ewm(span=50).mean()

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    tr = pd.concat([
        df['high'] - df['low'],
        abs(df['high'] - df['close'].shift()),
        abs(df['low'] - df['close'].shift())
    ], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()

    return df

# -------------------------------
# 3. فیلترها (همان منطق سیستم اصلی)
# -------------------------------
def check_structure(df):
    l, p, pp = df.iloc[-1], df.iloc[-2], df.iloc[-3]
    return {
        "long": (p['low'] > pp['low']) and (l['close'] > p['high']),
        "short": (p['high'] < pp['high']) and (l['close'] < p['low'])
    }

def detect_divergence(df):
    if len(df) < 5: return {"long": False, "short": False}
    low, high, rsi = df['low'].tail(5), df['high'].tail(5), df['rsi'].tail(5)
    return {
        "long": low.is_monotonic_decreasing and not rsi.is_monotonic_decreasing,
        "short": high.is_monotonic_increasing and not rsi.is_monotonic_increasing
    }

def detect_liquidity_grab(df):
    l, p = df.iloc[-1], df.iloc[-2]
    body_ratio = abs(p['open'] - p['close']) / (p['high'] - p['low']) if p['high'] != p['low'] else 0
    vol_avg = df['volume'].tail(10).mean()
    return {
        "long": (body_ratio < 0.3) and (l['close'] > l['open']) and (l['volume'] > 1.5 * vol_avg),
        "short": (body_ratio < 0.3) and (l['close'] < l['open']) and (l['volume'] > 1.5 * vol_avg)
    }

def confirm_volume(df):
    vol_avg = df['volume'].tail(20).mean()
    return {
        "long": df.iloc[-1]['volume'] > 1.5 * vol_avg,
        "short": df.iloc[-1]['volume'] > 1.5 * vol_avg
    }

# -------------------------------
# 4. شبیه‌سازی معاملات
# -------------------------------
def run_backtest(df):
    trades = []
    in_trade = False
    entry, sl, tp, side = 0, 0, 0, None

    for i in range(50, len(df)):
        temp_df = df.iloc[:i+1].copy()
        temp_df = add_indicators(temp_df)

        s = check_structure(temp_df)
        d = detect_divergence(temp_df)
        l = detect_liquidity_grab(temp_df)
        v = confirm_volume(temp_df)

        if not in_trade:
            if all([s['long'], d['long'], l['long'], v['long']]):
                entry = temp_df.iloc[-1]['close']
                sl = entry - 1.5 * temp_df.iloc[-1]['atr']
                tp = entry + 2 * (entry - sl)
                side = "long"
                in_trade = True
            elif all([s['short'], d['short'], l['short'], v['short']]):
                entry = temp_df.iloc[-1]['close']
                sl = entry + 1.5 * temp_df.iloc[-1]['atr']
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
# 5. گزارش و ارسال
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

💡 فیلترها: ساختار + واگرایی + نقدینگی + حجم
#بکتست #نهادی #اصولی
"""

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.post(url, data=data, timeout=10)
    except: pass

# -------------------------------
# 6. اجرای اصلی
# -------------------------------
def main():
    df = fetch_data()
    if len(df) < 100:
        msg = "❌ بک‌تست ناموفق: داده کافی دریافت نشد"
        print(msg)
        send_telegram(msg)
        return

    df = add_indicators(df)
    trades = run_backtest(df)
    report = generate_report(trades)
    print(report)
    send_telegram(report)

if __name__ == "__main__":
    main()
