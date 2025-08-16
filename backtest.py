# backtest.py
import pandas as pd
import os
from datetime import datetime
from data_handler import fetch_binance_data
from strategy import generate_signal
from telegram_bot import send_telegram_message
from logger_config import logger
import config

def backtest(symbol, start_date, end_date, timeframe='1h'):
    try:
        df = fetch_binance_data(symbol, timeframe, limit=1000, start_date=start_date, end_date=end_date)
        if df.empty or len(df) < 200:
            logger.warning("داده کافی موجود نیست")
            return

        signals = []
        wins = 0
        losses = 0
        RISK_REWARD = 2.0
        MAX_HOLD = 24  # حداکثر 24 کندل (24 ساعت)

        for i in range(200, len(df) - MAX_HOLD):
            window = df.iloc[:i+1]
            signal = generate_signal(window)

            if signal:
                entry = signal['entry']
                sl = signal['sl']
                tp = signal['tp']
                type_ = signal['type']

                # بررسی خروج
                exited = False
                for j in range(1, MAX_HOLD):
                    row = df.iloc[i + j]
                    if type_ == 'BUY':
                        if row['low'] <= sl:
                            losses += 1
                            exited = True
                            break
                        elif row['high'] >= tp:
                            wins += 1
                            exited = True
                            break
                    elif type_ == 'SELL':
                        if row['high'] >= sl:
                            losses += 1
                            exited = True
                            break
                        elif row['low'] <= tp:
                            wins += 1
                            exited = True
                            break
                if not exited:
                    final_price = df.iloc[i + MAX_HOLD - 1]['close']
                    if (type_ == 'BUY' and final_price > entry) or \
                       (type_ == 'SELL' and final_price < entry):
                        wins += 1
                    else:
                        losses += 1

                signals.append({
                    'type': type_,
                    'entry_bar': i,
                    'entry': entry,
                    'sl': sl,
                    'tp': tp,
                    'exit_bar': i + j if exited else i + MAX_HOLD - 1,
                    'status': 'win' if (exited and (type_ == 'BUY' and row['high'] >= tp or type_ == 'SELL' and row['low'] <= tp)) or (not exited and final_price > entry) else 'loss'
                })

        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0

        logger.info(f"📊 نتایج بک‌تست برای {symbol}")
        logger.info(f"📈 تعداد معاملات: {total}")
        logger.info(f"✅ موفق: {wins} | ❌ ناموفق: {losses}")
        logger.info(f"🎯 وین ریت: {win_rate:.1f}%")
        logger.info(f"🔁 نسبت R:R: {RISK_REWARD}:1")

        if config.TELEGRAM_TOKEN and config.CHAT_ID:
            msg = f"""
🚀 <b>استراتژی جدید: EMA200 + RSI Pullback</b>
📌 نماد: {symbol}
📅 بازه: {start_date} تا {end_date}
⏰ تایم‌فریم: {timeframe}

📈 تعداد معاملات: {total}
✅ موفق: {wins}
❌ ناموفق: {losses}
🎯 وین ریت: {win_rate:.1f}%
🔁 نسبت R:R: {RISK_REWARD}:1

✅ ورود در عقب‌نشینی روند
💡 هدف: سیگنال منظم + وین ریت بالا
"""
            send_telegram_message(config.TELEGRAM_TOKEN, config.CHAT_ID, msg)

        os.makedirs("results", exist_ok=True)
        pd.DataFrame(signals).to_csv(f"results/new_strategy_{symbol}_{start_date}_to_{end_date}.csv", index=False)
        logger.info("✅ نتایج ذخیره شد.")

    except Exception as e:
        logger.error(f"❌ خطای بک‌تست: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', type=str, required=True)
    parser.add_argument('--start', type=str, required=True)
    parser.add_argument('--end', type=str, required=True)
    parser.add_argument('--timeframe', type=str, default='1h')
    args = parser.parse_args()
    backtest(args.symbol, args.start, args.end, args.timeframe)
