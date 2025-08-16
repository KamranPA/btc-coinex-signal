# backtest.py
import argparse
import pandas as pd
import os
from datetime import datetime
from data_handler import fetch_kucoin_data
from strategy import generate_signal
from telegram_bot import send_telegram_message
from logger_config import logger
import config

def backtest(symbol, start_date, end_date, timeframe='1h'):
    try:
        df = fetch_kucoin_data(symbol, timeframe, limit=1000, start_date=start_date, end_date=end_date)
        if df.empty or len(df) < 200:
            logger.warning("داده کافی موجود نیست")
            return

        long_signals = []
        short_signals = []
        long_wins = 0
        long_losses = 0
        short_wins = 0
        short_losses = 0
        RISK_REWARD = 2.0
        MAX_HOLD = 24

        for i in range(200, len(df) - MAX_HOLD):
            window = df.iloc[:i+1]
            signals = generate_signal(window)

            if signals:
                for signal in signals:
                    entry = signal['entry']
                    sl = signal['sl']
                    tp = signal['tp']
                    type_ = signal['type']

                    exited = False
                    for j in range(1, MAX_HOLD):
                        row = df.iloc[i + j]
                        if type_ == 'BUY':
                            if row['low'] <= sl:
                                long_losses += 1
                                exited = True
                                break
                            elif row['high'] >= tp:
                                long_wins += 1
                                exited = True
                                break
                        elif type_ == 'SELL':
                            if row['high'] >= sl:
                                short_losses += 1
                                exited = True
                                break
                            elif row['low'] <= tp:
                                short_wins += 1
                                exited = True
                                break
                    if not exited:
                        final_price = df.iloc[i + MAX_HOLD - 1]['close']
                        if type_ == 'BUY':
                            if final_price > entry:
                                long_wins += 1
                            else:
                                long_losses += 1
                        elif type_ == 'SELL':
                            if final_price < entry:
                                short_wins += 1
                            else:
                                short_losses += 1

                    if type_ == 'BUY':
                        long_signals.append({
                            'entry_bar': i,
                            'entry': entry,
                            'sl': sl,
                            'tp': tp,
                            'exit_bar': i + j if exited else i + MAX_HOLD - 1,
                            'status': 'win' if (exited and row['high'] >= tp) or (not exited and final_price > entry) else 'loss'
                        })
                    else:
                        short_signals.append({
                            'entry_bar': i,
                            'entry': entry,
                            'sl': sl,
                            'tp': tp,
                            'exit_bar': i + j if exited else i + MAX_HOLD - 1,
                            'status': 'win' if (exited and row['low'] <= tp) or (not exited and final_price < entry) else 'loss'
                        })

        total_long = long_wins + long_losses
        total_short = short_wins + short_losses
        win_rate_long = (long_wins / total_long * 100) if total_long > 0 else 0
        win_rate_short = (short_wins / total_short * 100) if total_short > 0 else 0

        logger.info(f"📊 نتایج بک‌تست دوطرفه برای {symbol}")
        logger.info(f"📈 خرید (Long): {total_long} معامله | ✅ {long_wins} | ❌ {long_losses} | 🎯 {win_rate_long:.1f}%")
        logger.info(f"📉 فروش (Short): {total_short} معامله | ✅ {short_wins} | ❌ {short_losses} | 🎯 {win_rate_short:.1f}%")
        logger.info(f"🔁 نسبت R:R: {RISK_REWARD}:1")

        if config.TELEGRAM_TOKEN and config.CHAT_ID:
            msg = f"""
🚀 <b>سیستم دوطرفه: EMA200 + RSI Pullback</b>
📌 نماد: {symbol}
📅 بازه: {start_date} تا {end_date}
⏰ تایم‌فریم: {timeframe}

📈 <b>خرید (Long)</b>
• تعداد: {total_long}
• موفق: {long_wins}
• ناموفق: {long_losses}
• وین ریت: {win_rate_long:.1f}%

📉 <b>فروش (Short)</b>
• تعداد: {total_short}
• موفق: {short_wins}
• ناموفق: {short_losses}
• وین ریت: {win_rate_short:.1f}%

🔁 نسبت R:R: {RISK_REWARD}:1
💡 ورود در عقب‌نشینی روند
"""
            send_telegram_message(config.TELEGRAM_TOKEN, config.CHAT_ID, msg)
            logger.info("✅ نتایج به تلگرام ارسال شد.")

        os.makedirs("results", exist_ok=True)
        if long_signals:
            pd.DataFrame(long_signals).to_csv(f"results/long_{symbol}_{start_date}_to_{end_date}.csv", index=False)
        if short_signals:
            pd.DataFrame(short_signals).to_csv(f"results/short_{symbol}_{start_date}_to_{end_date}.csv", index=False)
        logger.info("✅ نتایج ذخیره شد.")

    except Exception as e:
        logger.error(f"❌ خطای بک‌تست: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', type=str, required=True)
    parser.add_argument('--start', type=str, required=True)
    parser.add_argument('--end', type=str, required=True)
    parser.add_argument('--timeframe', type=str, default='1h')
    args = parser.parse_args()
    backtest(args.symbol, args.start, args.end, args.timeframe)
