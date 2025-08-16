# backtest.py
import argparse
import pandas as pd
import os
from datetime import datetime
from data_handler import fetch_kucoin_data
from indicators import calculate_rsi, calculate_ema, calculate_macd
from risk_management import get_entry_sl_tp
from telegram_bot import send_telegram_message
from logger_config import logger
import config

def backtest(symbol, start_date, end_date, timeframe='15m'):
    try:
        df = fetch_kucoin_data(symbol, timeframe, limit=1000, start_date=start_date, end_date=end_date)
        if df.empty or len(df) < 50:
            logger.warning("داده کافی موجود نیست")
            return

        # محاسبه اندیکاتورها
        df['RSI'] = calculate_rsi(df['close'].values)
        df['EMA50'] = calculate_ema(df['close'].values, 50)
        df['MACD_LINE'], df['MACD_SIGNAL'] = calculate_macd(df['close'].values)
        df['VOL_MA20'] = df['volume'].rolling(20).mean()

        # پارامترها
        RISK_REWARD_RATIO = 2.0
        MAX_HOLD_BARS = 20

        signals = []
        wins = 0
        losses = 0

        for i in range(50, len(df) - MAX_HOLD_BARS):
            last = df.iloc[i]
            prev = df.iloc[i-1]

            # شرط اصلی: روند (فقط EMA50)
            uptrend = last['close'] > last['EMA50']
            downtrend = last['close'] < last['EMA50']

            # شرط اصلی: RSI
            rsi_buy_condition = prev['RSI'] <= 40 and last['RSI'] > 40  # خروج از نزول شدید
            rsi_sell_condition = prev['RSI'] >= 60 and last['RSI'] < 60  # خروج از صعود شدید

            # تأییدیه‌ها (اختیاری — امتیاز می‌دهند)
            macd_buy_ok = last['MACD_LINE'] > last['MACD_SIGNAL']
            macd_sell_ok = last['MACD_LINE'] < last['MACD_SIGNAL']
            volume_up = last['volume'] > 1.05 * last['VOL_MA20']

            # سیگنال خرید (فقط با روند و RSI)
            if not any(s['exit_bar'] is None for s in signals if s['type'] == 'BUY') and \
               uptrend and rsi_buy_condition:

                entry, sl, tp = get_entry_sl_tp("BUY", df.iloc[:i+1], risk_reward_ratio=RISK_REWARD_RATIO)
                signals.append({
                    'type': 'BUY',
                    'entry_bar': i,
                    'entry_price': entry,
                    'sl': sl,
                    'tp': tp,
                    'exit_bar': None,
                    'exit_price': None,
                    'status': 'open',
                    'score': 2 + (1 if macd_buy_ok else 0) + (1 if volume_up else 0)
                })

            # سیگنال فروش
            elif not any(s['exit_bar'] is None for s in signals if s['type'] == 'SELL') and \
                 downtrend and rsi_sell_condition:

                entry, sl, tp = get_entry_sl_tp("SELL", df.iloc[:i+1], risk_reward_ratio=RISK_REWARD_RATIO)
                signals.append({
                    'type': 'SELL',
                    'entry_bar': i,
                    'entry_price': entry,
                    'sl': sl,
                    'tp': tp,
                    'exit_bar': None,
                    'exit_price': None,
                    'status': 'open',
                    'score': 2 + (1 if macd_sell_ok else 0) + (1 if volume_up else 0)
                })

            # بررسی خروج
            for signal in signals:
                if signal['status'] == 'open':
                    future_df = df.iloc[i:i+MAX_HOLD_BARS]
                    for j, row in enumerate(future_df.itertuples()):
                        if signal['type'] == 'BUY':
                            if row.low <= signal['sl']:
                                signal['exit_bar'] = i + j
                                signal['exit_price'] = signal['sl']
                                signal['status'] = 'loss'
                                losses += 1
                                break
                            elif row.high >= signal['tp']:
                                signal['exit_bar'] = i + j
                                signal['exit_price'] = signal['tp']
                                signal['status'] = 'win'
                                wins += 1
                                break
                        elif signal['type'] == 'SELL':
                            if row.high >= signal['sl']:
                                signal['exit_bar'] = i + j
                                signal['exit_price'] = signal['sl']
                                signal['status'] = 'loss'
                                losses += 1
                                break
                            elif row.low <= signal['tp']:
                                signal['exit_bar'] = i + j
                                signal['exit_price'] = signal['tp']
                                signal['status'] = 'win'
                                wins += 1
                                break
                    else:
                        # خروج زمانی
                        last_row = df.iloc[i + MAX_HOLD_BARS - 1]
                        signal['exit_bar'] = i + MAX_HOLD_BARS - 1
                        signal['exit_price'] = last_row['close']
                        signal['status'] = 'timeout'
                        if signal['type'] == 'BUY':
                            if last_row['close'] > signal['entry_price']:
                                wins += 1
                            else:
                                losses += 1
                        else:
                            if last_row['close'] < signal['entry_price']:
                                wins += 1
                            else:
                                losses += 1

        # محاسبه وین ریت
        total_trades = wins + losses
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0

        logger.info(f"📊 نتایج بک‌تست برای {symbol}")
        logger.info(f"📈 تعداد کل سیگنال: {total_trades}")
        logger.info(f"✅ موفق: {wins} | ❌ ناموفق: {losses}")
        logger.info(f"🎯 وین ریت: {win_rate:.1f}%")

        # ارسال به تلگرام
        if config.TELEGRAM_TOKEN and config.CHAT_ID:
            msg = f"""
🚀 <b>بک‌تست نهایی (سیگنال منظم)</b>
📌 نماد: {symbol}
📅 بازه: {start_date} تا {end_date}
⏰ تایم‌فریم: {timeframe}

📈 تعداد معاملات: {total_trades}
✅ موفق: {wins}
❌ ناموفق: {losses}
🎯 وین ریت: {win_rate:.1f}%
🔁 نسبت R:R: {RISK_REWARD_RATIO}:1

✅ شرط اصلی: روند + RSI
✅ تأییدیه: MACD + حجم
💡 هدف: 3+ سیگنال در ماه با وین ریت > 50%
"""
            send_telegram_message(config.TELEGRAM_TOKEN, config.CHAT_ID, msg)
            logger.info("✅ نتایج به تلگرام ارسال شد.")

        # ذخیره نتایج
        os.makedirs("results", exist_ok=True)
        results_df = pd.DataFrame([
            {**s, 'symbol': symbol, 'timeframe': timeframe} for s in signals
        ])
        results_df.to_csv(f"results/backtest_{symbol}_{start_date}_to_{end_date}.csv", index=False)
        logger.info("✅ نتایج ذخیره شد.")

    except Exception as e:
        logger.error(f"❌ خطای بک‌تست: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--symbol', type=str, required=True)
    parser.add_argument('--start', type=str, required=True)
    parser.add_argument('--end', type=str, required=True)
    parser.add_argument('--timeframe', type=str, default='15m')
    args = parser.parse_args()

    backtest(args.symbol, args.start, args.end, args.timeframe)
