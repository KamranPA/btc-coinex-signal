# backtest.py
import argparse
import pandas as pd
import os
from datetime import datetime
from data_handler import fetch_kucoin_data
from indicators import calculate_rsi, calculate_macd, calculate_ema
from risk_management import get_entry_sl_tp
from telegram_bot import send_telegram_message
from logger_config import logger
import config

def backtest(symbol, start_date, end_date, timeframe='15m', higher_timeframe='1h'):
    try:
        # داده اصلی (تایم‌فریم پایین)
        df = fetch_kucoin_data(symbol, timeframe, limit=500, start_date=start_date, end_date=end_date)
        if df.empty or len(df) < 50:
            logger.warning("داده کافی موجود نیست")
            return

        # داده روند (تایم‌فریم بالاتر)
        df_htf = fetch_kucoin_data(symbol, higher_timeframe, limit=100)
        if df_htf.empty:
            logger.warning("داده تایم‌فریم بالاتر موجود نیست")
            return

        # محاسبه اندیکاتورها
        df['RSI'] = calculate_rsi(df['close'].values)
        df['EMA50'] = calculate_ema(df['close'].values, 50)
        df['VOL_MA20'] = df['volume'].rolling(20).mean()

        # فیلتر روند از تایم‌فریم بالاتر
        last_close_htf = df_htf['close'].iloc[-1]
        ema50_htf = calculate_ema(df_htf['close'].values, 50)[-1]
        uptrend = last_close_htf > ema50_htf
        downtrend = last_close_htf < ema50_htf

        signals = []
        for i in range(1, len(df)):
            last = df.iloc[i]
            prev = df.iloc[i-1]

            volume_condition = last['volume'] > 1.1 * last['VOL_MA20']  # فقط +10%
            rsi_buy_condition = prev['RSI'] <= 35 and last['RSI'] > 35
            rsi_sell_condition = prev['RSI'] >= 65 and last['RSI'] < 65

            # سیگنال خرید
            if (uptrend and
                rsi_buy_condition and
                volume_condition):
                entry, sl, tp = get_entry_sl_tp("BUY", df.iloc[:i+1])
                signals.append({
                    'type': 'BUY',
                    'time': last.name,
                    'entry': entry,
                    'sl': sl,
                    'tp': tp,
                    'rsi': last['RSI'],
                    'score': 3  # قوی
                })

            # سیگنال فروش
            elif (downtrend and
                  rsi_sell_condition and
                  volume_condition):
                entry, sl, tp = get_entry_sl_tp("SELL", df.iloc[:i+1])
                signals.append({
                    'type': 'SELL',
                    'time': last.name,
                    'entry': entry,
                    'sl': sl,
                    'tp': tp,
                    'rsi': last['RSI'],
                    'score': 3
                })

        logger.info(f"✅ {len(signals)} سیگنال قوی یافت شد.")

        # ارسال به تلگرام
        if signals and config.TELEGRAM_TOKEN and config.CHAT_ID:
            msg = f"""
🎯 <b>سیگنال‌های بهینه‌شده</b>
📌 نماد: {symbol}
📅 بازه: {start_date} تا {end_date}
⏰ تایم‌فریم: {timeframe}
📈 تعداد: {len(signals)}

📝 سیگنال‌ها (R:R > 1.5):
"""
            for sig in signals[:5]:
                msg += f"""
• {sig['type']} | {sig['time']} | ورود: {sig['entry']} | SL: {sig['sl']} | TP: {sig['tp']}
"""
            send_telegram_message(config.TELEGRAM_TOKEN, config.CHAT_ID, msg)
            logger.info("✅ سیگنال‌ها به تلگرام ارسال شد.")

        # ذخیره
        os.makedirs("results", exist_ok=True)
        df.to_csv(f"results/{symbol}_{start_date}_to_{end_date}.csv")
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
