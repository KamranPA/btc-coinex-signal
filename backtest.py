# backtest.py
import datetime
import pandas as pd
import ccxt
import requests
import json

# -------------------------------
# تنظیمات بک‌تست
# -------------------------------
START_DATE = '2025-04-01'      # ← برای تست تغییر دهید
END_DATE = '2025-05-01'
SYMBOL = 'BTC/USDT'
TIMEFRAME = '15m'

# توکن تلگرام — خودتان وارد کنید
TELEGRAM_TOKEN = "8205878716:AAFOSGnsF1gnY3kww1WvPT0HYubCkyPaC64"
TELEGRAM_CHAT_ID = "104506829"

# -------------------------------
# 1. دریافت داده از KuCoin
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

    df['ema20'] = df['close'].ewm(span=20).mean()
    df['ema50'] = df['close'].ewm(span=50).mean()
    df['ema200'] = df['close'].ewm(span=200).mean()

    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()

    df['vwap'] = ((df['high'] + df['low'] + df['close']) / 3 * df['volume']).cumsum() / df['volume'].cumsum()

    return df

# -------------------------------
# 3. شبیه‌سازی apply_filters.py (نسخه بهینه دوطرفه)
# -------------------------------
def evaluate_filters(df):
    i = len(df) - 1
    l = df.iloc[-1]
    p = df.iloc[-2] if len(df) > 1 else None
    if p is None or i < 50:
        return {"long": False, "short": False, "details": {}}

    volume_avg = df['volume'].tail(20).mean()
    atr_ratio = l['atr'] / l['close']

    # Long Conditions
    long_conditions = {
        "trend_up": l['ema20'] > l['ema50'] > l['ema200'],
        "price_above_ema20": l['close'] > l['ema20'],
        "volume_spike": l['volume'] > 1.3 * volume_avg,
        "volatility_ok": atr_ratio > 0.003,
        "rsi_ok": 35 < l['rsi'] < 60,
        "bullish_candle": l['close'] > l['open'],
        "strong_body": abs(l['close'] - l['open']) / (l['high'] - l['low']) > 0.5,
        "higher_lows": l['low'] > p['low'],
        "above_vwap": l['close'] > l['vwap'],
        "rsi_divergence": False
    }

    # Short Conditions
    short_conditions = {
        "trend_down": l['ema20'] < l['ema50'] < l['ema200'],
        "price_below_ema20": l['close'] < l['ema20'],
        "volume_spike": l['volume'] > 1.3 * volume_avg,
        "volatility_ok": atr_ratio > 0.003,
        "rsi_ok": 40 < l['rsi'] < 65,
        "bearish_candle": l['close'] < l['open'],
        "strong_body": abs(l['close'] - l['open']) / (l['high'] - l['low']) > 0.5,
        "lower_highs": l['high'] < p['high'],
        "below_vwap": l['close'] < l['vwap'],
        "rsi_divergence": False
    }

    # واگرایی
    if i > 5:
        recent_lows = df['low'].iloc[-5:]
        recent_highs = df['high'].iloc[-5:]
        recent_rsi = df['rsi'].iloc[-5:]

        if recent_lows.is_monotonic_increasing and not recent_rsi.is_monotonic_increasing:
            long_conditions["rsi_divergence"] = True
        if recent_highs.is_monotonic_decreasing and not recent_rsi.is_monotonic_decreasing:
            short_conditions["rsi_divergence"] = True

    long_score = sum(long_conditions.values())
    short_score = sum(short_conditions.values())
    required = 7  # حداقل 7 فیلتر

    return {
        "long": long_score >= required,
        "short": short_score >= required,
        "details": {
            "long": long_conditions,
            "short": short_conditions
        }
    }

# -------------------------------
# 4. شبیه‌سازی make_decision.py
# -------------------------------
def make_decision(filters_result, ml_score, df):
    # فرض: ML Score همیشه 0.75 (میانگین مدل)
    # یا می‌توانید از یک قانون ساده استفاده کنید
    ml_score = 0.75
    threshold = 0.7
    l = df.iloc[-1]

    if filters_result['long'] and ml_score >= threshold:
        return {
            "action": "buy",
            "entry": l['close'],
            "direction": "long"
        }
    elif filters_result['short'] and ml_score >= threshold:
        return {
            "action": "sell",
            "entry": l['close'],
            "direction": "short"
        }
    else:
        return {"action": "hold"}

# -------------------------------
# 5. شبیه‌سازی calculate_risk.py
# -------------------------------
def calculate_risk(df, entry_price, direction="long"):
    l = df.iloc[-1]
    atr = l['atr']
    
    if direction == "long":
        support = df['low'].rolling(10).min().iloc[-1]
        sl = min(entry_price - (1.5 * atr), support * 0.99)
        tp = entry_price + 2 * (entry_price - sl)
        rr = (tp - entry_price) / (entry_price - sl) if entry_price > sl else 0
    else:
        resistance = df['high'].rolling(10).max().iloc[-1]
        sl = max(entry_price + (1.5 * atr), resistance * 1.01)
        tp = entry_price - 2 * (sl - entry_price)
        rr = (entry_price - tp) / (sl - entry_price) if sl > entry_price else 0

    return {
        "sl": round(sl, 2),
        "tp": round(tp, 2),
        "risk_reward": round(rr, 2),
        "rr_ok": rr >= 1.8
    }

# -------------------------------
# 6. شبیه‌سازی معاملات
# -------------------------------
def run_backtest(df):
    trades = []
    in_trade = False
    entry_price = 0
    sl_price = 0
    tp_price = 0
    trade_side = None

    for i in range(50, len(df)):
        temp_df = df.iloc[:i+1].copy()
        temp_df = add_indicators(temp_df)
        
        filters = evaluate_filters(temp_df)
        decision = make_decision(filters, 0.75, temp_df)
        l = temp_df.iloc[-1]

        if not in_trade and decision["action"] != "hold":
            entry_price = decision["entry"]
            risk_data = calculate_risk(temp_df, entry_price, decision["direction"])
            
            if not risk_data["rr_ok"]:
                continue

            sl_price = risk_data["sl"]
            tp_price = risk_data["tp"]
            trade_side = decision["direction"]
            in_trade = True

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
# 7. گزارش و ارسال
# -------------------------------
def generate_report(trades):
    if not trades:
        return f"📊 بک‌تست: هیچ معامله‌ای در دوره <b>{START_DATE}</b> تا <b>{END_DATE}</b> انجام نشد."

    wins = [t for t in trades if t['type'] == 'win']
    win_rate = len(wins) / len(trades) * 100

    return f"""
📊 <b>گزارش بک‌تست سیستم اصلی</b>
📆 دوره: {START_DATE} تا {END_DATE}
📌 جفت: {SYMBOL}
⏱ تایم‌فریم: {TIMEFRAME}

🔢 تعداد معاملات: {len(trades)}
✅ سودآور: {len(wins)}
❌ ضررده: {len(trades) - len(wins)}
🎯 نرخ موفقیت: {win_rate:.1f}%
🔄 سیستم: دوطرفه (Long & Short)

#بکتست #سیگنال #حرفه‌ای
"""

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
# 8. اجرای اصلی
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
