# backtest.py
import datetime
import pandas as pd
import ccxt
import requests
import os

# -------------------------------
# 1. دریافت بازه زمانی از ورودی GitHub
# -------------------------------
START_DATE = os.getenv('START_DATE', '2023-01-01')
END_DATE = os.getenv('END_DATE', '2023-02-01')

# تنظیمات
SYMBOL = 'BTC/USDT'
TIMEFRAME = '15m'

# توکن و چت آیدی تلگرام — خودتان وارد کنید
TELEGRAM_TOKEN = "7123456789:AAHd123abcDEFgh456ijk789LMNOPqrstuv"  # ← عوض کنید
TELEGRAM_CHAT_ID = "123456789"  # ← عوض کنید

# پارامترهای معامله
SL_ATR_MULTIPLIER = 1.5
TP_RR_RATIO = 2.0

# -------------------------------
# 2. دریافت داده با محدودیت زمانی
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
    if df.empty:
        return df
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[(df['timestamp'] >= START_DATE) & (df['timestamp'] < END_DATE)]
    df.reset_index(drop=True, inplace=True)
    print(f"✅ {len(df)} کندل دریافت شد از {START_DATE} تا {END_DATE}")
    return df

# -------------------------------
# 3. محاسبه اندیکاتورها
# -------------------------------
def add_indicators(df):
    if df is None or len(df) < 50:
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
# 4. ارزیابی فیلترها
# -------------------------------
def is_signal(df, i):
    l = df.iloc[i]
    p = df.iloc[i-1] if i > 0 else None
    if p is None or pd.isna(l['rsi']):
        return False

    volume_window = df['volume'].iloc[max(0, i-20):i]
    volume_avg = volume_window.mean() if len(volume_window) > 0 else 0

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
# 5. شبیه‌سازی معاملات
# -------------------------------
def run_backtest(df):
    trades = []
    in_trade = False
    entry_price = 0
    sl_price = 0
    tp_price = 0
    trade_start_time = None

    for i in range(50, len(df)):
        if not in_trade and is_signal(df, i):
            entry_price = df['close'].iloc[i]
            atr = df['atr'].iloc[i]
            support = df['low'].iloc[max(0, i-10):i].min() if i > 10 else df['low'].iloc[0:i].min()
            
            sl_price = min(entry_price - (SL_ATR_MULTIPLIER * atr), support * 0.99)
            tp_price = entry_price + TP_RR_RATIO * (entry_price - sl_price)
            trade_start_time = df['timestamp'].iloc[i]
            in_trade = True

        elif in_trade:
            low = df['low'].iloc[i]
            high = df['high'].iloc[i]
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
                in_trade = False

    return trades

# -------------------------------
# 6. تولید گزارش
# -------------------------------
def generate_report(trades):
    if not trades:
        return f"📊 بک‌تست: هیچ سیگنالی در بازه <b>{START_DATE}</b> تا <b>{END_DATE}</b> فعال نشد."

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
# 7. ارسال به تلگرام
# -------------------------------
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("✅ گزارش بک‌تست به تلگرام ارسال شد")
        else:
            print(f"❌ وضعیت ارسال: {response.status_code}")
    except Exception as e:
        print(f"❌ ارسال ناموفق: {str(e)}")

# -------------------------------
# 8. اجرای اصلی
# -------------------------------
def main():
    print(f"🔄 شروع بک‌تست: {START_DATE} تا {END_DATE}")
    df = fetch_data()
    if df is None or len(df) < 100:
        report = f"❌ بک‌تست ناموفق: داده کافی دریافت نشد برای دوره {START_DATE} تا {END_DATE}"
        print(report)
        send_telegram(report)
        return

    df = add_indicators(df)
    trades = run_backtest(df)
    report = generate_report(trades)
    print(report)
    send_telegram(report)

if __name__ == "__main__":
    main()
