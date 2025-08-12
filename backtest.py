# backtest.py
import datetime
import pandas as pd
import ccxt
import requests
import json

# -------------------------------
# تنظیمات بک‌تست
# -------------------------------
SYMBOL = 'BTC/USDT'
TIMEFRAME = '15m'
START_DATE = '2025-03-01'  # ⏰ تاریخ شروع (دلخواه)
END_DATE = '2025-04-01'    # ⏰ تاریخ پایان (دلخواه)

# توکن و چت آیدی تلگرام — خودتان وارد کنید
TELEGRAM_TOKEN = "8205878716:AAFOSGnsF1gnY3kww1WvPT0HYubCkyPaC64"  # ← عوض کنید
TELEGRAM_CHAT_ID = "104506829"  # ← عوض کنید

# پارامترهای معامله
SL_ATR_MULTIPLIER = 1.5
TP_RR_RATIO = 2.0

# -------------------------------
# 1. دریافت داده با محدودیت زمانی
# -------------------------------
def fetch_data():
    exchange = ccxt.coinex({'enableRateLimit': True})
    since = exchange.parse8601(START_DATE + 'T00:00:00Z')
    end = exchange.parse8601(END_DATE + 'T00:00:00Z')
    
    all_ohlcv = []
    while since < end:
        try:
            ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, since, limit=1000)
            if not ohlcv:
                break
            since = ohlcv[-1][0] + 1
            all_ohlcv.extend(ohlcv)
        except Exception as e:
            print(f"❌ خطا در دریافت داده: {str(e)}")
            break

    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[(df['timestamp'] >= START_DATE) & (df['timestamp'] < END_DATE)]
    print(f"✅ {len(df)} کندل دریافت شد از {START_DATE} تا {END_DATE}")
    return df

# -------------------------------
# 2. محاسبه اندیکاتورها
# -------------------------------
def add_indicators(df):
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
# 3. ارزیابی فیلترها
# -------------------------------
def is_signal(df, i):
    l = df.iloc[i]
    p = df.iloc[i-1] if i > 0 else None
    if p is None:
        return False

    volume_avg = df['volume'].iloc[max(0, i-20):i].mean() if i > 20 else df['volume'].iloc[:i].mean()

    filters = {
        "trend": l['ema20'] > l['ema50'] > l['ema200'],
        "price_above_ema200": l['close'] > l['ema200'],
        "volume_spike": l['volume'] > 1.3 * volume_avg,
        "high_volatility": l['atr'] > 0.003 * l['close'],
        "rsi_ok": 30 < l['rsi'] < 70,
        "structure": l['low'] > p['low'] if l['close'] > l['open'] else False
    }

    return all(filters.values())

# -------------------------------
# 4. شبیه‌سازی معاملات
# -------------------------------
def run_backtest(df):
    trades = []
    in_trade = False
    entry_price = 0
    sl_price = 0
    tp_price = 0
    trade_start_time = None

    for i in range(50, len(df)):  # شروع از کندل 50 برای اندیکاتور
        if not in_trade and is_signal(df, i):
            entry_price = df['close'].iloc[i]
            atr = df['atr'].iloc[i]
            support = df['low'].iloc[i-10:i].min()
            
            sl_price = min(entry_price - (SL_ATR_MULTIPLIER * atr), support * 0.99)
            tp_price = entry_price + TP_RR_RATIO * (entry_price - sl_price)
            trade_start_time = df['timestamp'].iloc[i]
            in_trade = True
            print(f"📌 ورود در {entry_price} در {trade_start_time}")

        elif in_trade:
            low = df['low'].iloc[i]
            high = df['high'].iloc[i]
            close = df['close'].iloc[i]
            time = df['timestamp'].iloc[i]

            if low <= sl_price:
                trades.append({
                    'entry': entry_price,
                    'exit': sl_price,
                    'type': 'loss',
                    'profit': -1,
                    'duration': (time - trade_start_time).total_seconds() / 3600,
                    'time': time
                })
                print(f"⛔ خروج با ضرر در {sl_price}")
                in_trade = False
            elif high >= tp_price:
                trades.append({
                    'entry': entry_price,
                    'exit': tp_price,
                    'type': 'win',
                    'profit': 1,
                    'duration': (time - trade_start_time).total_seconds() / 3600,
                    'time': time
                })
                print(f"🎯 خروج با سود در {tp_price}")
                in_trade = False

    return trades

# -------------------------------
# 5. تولید گزارش
# -------------------------------
def generate_report(trades):
    if not trades:
        return "📊 بک‌تست: هیچ سیگنالی فعال نشد."

    wins = [t for t in trades if t['type'] == 'win']
    win_rate = len(wins) / len(trades) * 100
    avg_duration = sum(t['duration'] for t in trades) / len(trades)

    report = f"""
📈 <b>گزارش بک‌تست سیستم سیگنال</b>
📆 دوره: {START_DATE} تا {END_DATE}
📌 جفت: {SYMBOL}
⏱ تایم‌فریم: {TIMEFRAME}

🔢 تعداد معاملات: {len(trades)}
✅ معاملات سودآور: {len(wins)}
❌ معاملات ضررده: {len(trades) - len(wins)}
🎯 نرخ موفقیت: {win_rate:.1f}%
⏱ میانگین مدت معامله: {avg_duration:.2f} ساعت

#بکتست #سیگنال #بیتکوین
"""
    return report.strip()

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
        print("✅ گزارش بک‌تست به تلگرام ارسال شد")
    except Exception as e:
        print(f"❌ ارسال ناموفق: {str(e)}")

# -------------------------------
# 7. اجرای اصلی
# -------------------------------
def main():
    print("🔄 شروع بک‌تست...")
    df = fetch_data()
    if len(df) < 100:
        print("❌ داده کافی نیست")
        return

    df = add_indicators(df)
    trades = run_backtest(df)
    report = generate_report(trades)
    print(report)
    send_telegram(report)

if __name__ == "__main__":
    main()
