# backtest.py
import argparse
import pandas as pd
import os
from datetime import datetime
from data_handler import fetch_binance_data
from indicators import calculate_rsi, calculate_macd, calculate_ema
from risk_management import get_entry_sl_tp
from telegram_bot import send_telegram_message
from logger_config import logger
import config

def backtest(symbol, start_date, end_date, timeframe='15m'):
    try:
        df = fetch_binance_data(symbol, timeframe, start_date=start_date, end_date=end_date)
        if len(df) < 50:
            logger.warning("داده کافی موجود نیست")
            return

        # محاسبه اندیکاتورها
        df['RSI'] = calculate_rsi(df['close'].values)
        df['MACD_LINE'], df['MACD_SIGNAL'] = calculate_macd(df['close'].values)
        df['EMA50'] = calculate_ema(df['close'].values, 50)
        df['VOL_MA20'] = df['volume'].rolling(20).mean()

        # بررسی سیگنال‌ها
        signals = []
        for i in range(1, len(df)):
            last = df.iloc[i]
            prev = df.iloc[i-1]

            volume_condition = last['volume'] > 1.2 * last['VOL_MA20']

            # سیگنال خرید
            if (last['close'] > last['EMA50'] and
                last['MACD_LINE'] > last['MACD_SIGNAL'] and
                prev['RSI'] <= 30 and last['RSI'] > 30 and
                volume_condition):
                entry, sl, tp = get_entry_sl_tp("BUY", df.iloc[:i+1])
                signals.append({
                    'type': 'BUY',
                    'time': last.name,
                    'entry': entry,
                    'sl': sl,
                    'tp': tp,
                    'rsi': last['RSI'],
                    'macd': last['MACD_LINE']
                })

            # سیگنال فروش
            elif (last['close'] < last['EMA50'] and
                  last['MACD_LINE'] < last['MACD_SIGNAL'] and
                  prev['RSI'] >= 70 and last['RSI'] < 70 and
                  volume_condition):
                entry, sl, tp = get_entry_sl_tp("SELL", df.iloc[:i+1])
                signals.append({
                    'type': 'SELL',
                    'time': last.name,
                    'entry': entry,
                    'sl': sl,
                    'tp': tp,
                    'rsi': last['RSI'],
                    'macd': last['MACD_LINE']
                })

        # ارسال نتایج به تلگرام
        if signals:
            msg = f"""
📊 <b>نتیجه بک‌تست</b>
📌 نماد: {symbol}
📅 بازه زمانی: {start_date} تا {end_date}
⏰ تایم‌فریم: {timeframe}
📈 تعداد سیگنال: {len(signals)}

📝 سیگنال‌ها:
"""
            for sig in signals[:5]:  # فقط 5 تا نمایش ده
                msg += f"""
• {sig['type']} | زمان: {sig['time']} | قیمت ورود: {sig['entry']} | SL: {sig['sl']} | TP: {sig['tp']}
"""
            send_telegram_message(config.TELEGRAM_TOKEN, config.CHAT_ID, msg)
            logger.info(f"✅ نتیجه بک‌تست به تلگرام ارسال شد.")

        # ذخیره نتایج در results/
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        filename = f"{symbol}_{start_date}_to_{end_date}.csv"
        df.to_csv(os.path.join(results_dir, filename))
        logger.info(f"✅ نتایج بک‌تست ذخیره شد: {filename}")

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
