# backtest.py
import datetime
import pandas as pd
import ccxt
import requests
import os

# -------------------------------
# تنظیمات اصلی — فقط اینجا را ویرایش کنید
# -------------------------------
START_DATE = '2025-04-01'      # تاریخ شروع بک‌تست
END_DATE = '2025-05-01'        # تاریخ پایان بک‌تест
SYMBOL = 'BTC/USDT'
TIMEFRAME = '15m'

# اطلاعات ربات تلگرام
TELEGRAM_TOKEN = "7123456789:AAHd123abcDEFgh456ijk789LMNOPqrstuv"  # ← عوض کنید
TELEGRAM_CHAT_ID = "123456789"  # ← عوض کنید

# پارامترهای معامله
SL_ATR_MULTIPLIER = 1.5
TP_RR_RATIO = 2.0

# -------------------------------
# 1. دریافت داده از KuCoin (بدون محدودیت)
# -------------------------------
def fetch_data():
    exchange = ccxt.kucoin({
        'enableRateLimit': True,
        'rateLimit': 2000
    })
    since = exchange.parse8601(f"{START_DATE}T00:00:00Z")
    end = exchange.parse8601(f"{END_DATE}T00:00:00Z")
    
    all_ohlcv = []
    while since < end:
        try:
            ohlcv = exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, since, limit=500)
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
    print(f"✅ {len(df)} کندل دریافت شد")
    return df

# -------------------------------
# 2. محاسبه اندیکاتورها
# -------------------------------
def add_indicators(df):
    if len(df) < 50:
        return df

    # EMA
    df['ema20'] = df['close'].ewm(span=20).mean()
    df['ema50'] = df['close'].ewm(span=50).mean()
    df['ema200'] = df['close'].ewm(span=200).mean()

    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # ATR
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()

    # VWAP
    df['vwap'] = ((df['high'] + df['low'] + df['close']) / 3 * df['volume']).cumsum() / df['volume'].cumsum()

    return df

# -------------------------------
# 3. تشخیص سیگنال دوطرفه (Long و Short)
# -------------------------------
def is_signal(df, i):
    l = df.iloc[i]
    p = df.iloc[i-1] if i > 0 else None
    if p is None or pd.isna(l['rsi']):
        return None

    volume_avg = df['volume'].iloc[max(0, i-20):i].mean() if i > 20 else df['volume'].mean()
    atr_ratio = l['atr'] / l['close']

    # -------------------------------
    # فیلترهای صعودی (Long)
    # -------------------------------
    long_conditions = {
        "trend_up": l['ema20'] > l['ema50'] > l['ema200'],
        "price_above_ema": l['close'] > l['ema20'],
        "volume_spike": l['volume'] > 1.3 * volume_avg,
        "volatility_ok": atr_ratio > 0.003,
        "rsi_ok": 35 < l['rsi'] < 60,
        "bullish_candle": l['close'] > l['open'],
        "strong_body": abs(l['close'] - l['open']) / (l['high'] - l['low']) > 0.5,
        "higher_lows": l['low'] > p['low'],
        "above_vwap": l['close'] > l['vwap'] * 0.99,
        "rsi_divergence": False  # در حلقه اصلی محاسبه می‌شود
    }

    # -------------------------------
    # فیلترهای نزولی (Short)
    # -------------------------------
    short_conditions = {
        "trend_down": l['ema20'] < l['ema50'] < l['ema200'],
        "price_below_ema": l['close'] < l['ema20'],
        "volume_spike": l['volume'] > 1.3 * volume_avg,
        "volatility_ok": atr_ratio > 0.003,
        "rsi_ok": 40 < l['rsi'] < 65,
        "bearish_candle": l['close'] < l['open'],
        "strong_body": abs(l['close'] - l['open']) / (l['high'] - l['low']) > 0.5,
        "lower_highs": l['high'] < p['high'],
        "below_vwap": l['close'] < l['vwap'] * 1.01,
        "rsi_divergence": False
    }

    # محاسبه واگرایی (5 کندل اخیر)
    if i > 5:
        recent_lows = df['low'].iloc[i-5:i]
        recent_highs = df['high'].iloc[i-5:i]
        recent_rsi = df['rsi'].iloc[i-5:i]

        # واگرایی صعودی (Long)
        if recent_lows.is_monotonic_increasing and not recent_rsi.is_monotonic_increasing:
            long_conditions["rsi_divergence"] = True

        # واگرایی نزولی (Short)
        if recent_highs.is_monotonic_decreasing and not recent_rsi.is_monotonic_decreasing:
            short_conditions["rsi_divergence"] = True

    # بررسی Long
    long_score = sum(long_conditions.values())
    if long_score >= 7:
        return {"side": "long", "entry": l['close'], "conditions": long_conditions}

    # بررسی Short
    short_score = sum(short_conditions.values())
    if short_score >= 7:
        return {"side": "short", "entry": l['close'], "conditions": short_conditions}

    return None

# -------------------------------
# 4. شبیه‌سازی معاملات
# -------------------------------
def run_backtest(df):
    trades = []
    in_trade = False
    entry_price = 0
    sl_price = 0
    tp_price = 0
    trade_side = None
    trade_start_time = None

    for i in range(50, len(df)):
        signal = is_signal(df, i)
        l = df.iloc[i]

        # ورود
        if not in_trade and signal:
            entry_price = signal['entry']
            atr = l['atr']
            trade_side = signal['side']
            trade_start_time = l['timestamp']

            if trade_side == "long":
                support = df['low'].iloc[max(0, i-10):i].min()
                sl_price = min(entry_price - (SL_ATR_MULTIPLIER * atr), support * 0.99)
                tp_price = entry_price + TP_RR_RATIO * (entry_price - sl_price)
            else:  # short
                resistance = df['high'].iloc[max(0, i-10):i].max()
                sl_price = max(entry_price + (SL_ATR_MULTIPLIER * atr), resistance * 1.01)
                tp_price = entry_price - TP_RR_RATIO * (sl_price - entry_price)

            in_trade = True
            print(f"📌 ورود {trade_side} در {entry_price}")

        # خروج
        elif in_trade:
            low = l['low']
            high = l['high']
            time = l['timestamp']

            if trade_side == "long":
                if low <= sl_price:
                    trades.append({"type": "loss", "side": "long", "time": time})
                    in_trade = False
                elif high >= tp_price:
                    trades.append({"type": "win", "side": "long", "time": time})
                    in_trade = False
            else:
                if high >= sl_price:
                    trades.append({"type": "loss", "side": "short", "time": time})
                    in_trade = False
                elif low <= tp_price:
                    trades.append({"type": "win", "side": "short", "time": time})
                    in_trade = False

    return trades

# -------------------------------
# 5. تولید گزارش
# -------------------------------
def generate_report(trades):
    if not trades:
        return f"📊 بک‌تست: هیچ سیگنالی در دوره <b>{START_DATE}</b> تا <b>{END_DATE}</b> تولید نشد."

    longs = [t for t in trades if t['side'] == 'long']
    shorts = [t for t in trades if t['side'] == 'short']
    wins = [t for t in trades if t['type'] == 'win']
    losses = [t for t in trades if t['type'] == 'loss']

    win_rate = len(wins) / len(trades) * 100 if trades else 0

    return f"""
🚀 <b>گزارش بک‌تست دوطرفه</b>
📅 دوره: {START_DATE} تا {END_DATE}
📌 جفت: {SYMBOL}
⏱ تایم‌فریم: {TIMEFRAME}

🔢 کل معاملات: {len(trades)}
🟢 لانگ: {len(longs)}
🔴 شورت: {len(shorts)}
✅ سودآور: {len(wins)}
❌ ضررده: {len(losses)}
🎯 نرخ موفقیت: {win_rate:.1f}%

#بکتست #سیگنال #دوطرفه
"""

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
    print(f"🔄 شروع بک‌تست: {START_DATE} تا {END_DATE}")
    df = fetch_data()
    if len(df) < 100:
        error = f"❌ بک‌تست ناموفق: داده کافی دریافت نشد ({len(df)} کندل)"
        print(error)
        send_telegram(error)
        return

    df = add_indicators(df)
    trades = run_backtest(df)
    report = generate_report(trades)
    print(report)
    send_telegram(report)

if __name__ == "__main__":
    main()
