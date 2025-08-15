# main.py (اصلاح شده برای GitHub Actions)
import time
import schedule
import pandas as pd
from datetime import datetime, timezone, time as dt_time
import logging

from data_handler import fetch_binance_data
from indicators import calculate_rsi, calculate_macd, calculate_ema
from risk_management import get_entry_sl_tp
from telegram_bot import send_telegram_message
from logger_config import logger
import config

def is_market_active():
    now_utc = datetime.now(timezone.utc).time()
    start_block = dt_time(8, 30)
    end_block = dt_time(3, 0)
    if start_block <= now_utc or now_utc <= end_block:
        return False
    return True

def check_signal():
    if not is_market_active():
        logger.info("🚫 سیستم در این بازه زمانی غیرفعال است (8:30 تا 3 UTC)")
        return

    try:
        df = fetch_binance_data(config.SYMBOL, config.TIMEFRAME, limit=100)
        if len(df) < 50:
            logger.warning("داده کافی موجود نیست")
            return

        # محاسبه اندیکاتورها
        df['RSI'] = calculate_rsi(df['close'].values)
        df['MACD_LINE'], df['MACD_SIGNAL'] = calculate_macd(df['close'].values)
        df['EMA50'] = calculate_ema(df['close'].values, 50)
        df['VOL_MA20'] = df['volume'].rolling(20).mean()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        volume_condition = last['volume'] > 1.2 * last['VOL_MA20']

        # بررسی سیگنال خرید
        if (last['close'] > last['EMA50'] and
            last['MACD_LINE'] > last['MACD_SIGNAL'] and
            prev['RSI'] <= 30 and last['RSI'] > 30 and
            volume_condition):

            entry, sl, tp = get_entry_sl_tp("BUY", df)
            msg = f"""
🟢 <b>سیگنال خرید</b>
📌 نماد: {config.SYMBOL}
🕒 زمان: {last.name}
📊 قیمت ورود: {entry}
🛑 حد ضرر: {sl}
🎯 حد سود: {tp}
🧮 RSI: {last['RSI']:.1f}
🔵 MACD: {last['MACD_LINE']:.4f} | سیگنال: {last['MACD_SIGNAL']:.4f}
📈 حجم: {last['volume']:.0f} (میانگین: {last['VOL_MA20']:.0f})
            """
            send_telegram_message(config.TELEGRAM_TOKEN, config.CHAT_ID, msg)
            logger.info(f"BUY سیگنال ارسال شد: {entry} | SL: {sl} | TP: {tp}")

        # بررسی سیگنال فروش
        elif (last['close'] < last['EMA50'] and
              last['MACD_LINE'] < last['MACD_SIGNAL'] and
              prev['RSI'] >= 70 and last['RSI'] < 70 and
              volume_condition):

            entry, sl, tp = get_entry_sl_tp("SELL", df)
            msg = f"""
🔴 <b>سیگنال فروش</b>
📌 نماد: {config.SYMBOL}
🕒 زمان: {last.name}
📊 قیمت ورود: {entry}
🛑 حد ضرر: {sl}
🎯 حد سود: {tp}
🧮 RSI: {last['RSI']:.1f}
🔴 MACD: {last['MACD_LINE']:.4f} | سیگنال: {last['MACD_SIGNAL']:.4f}
📉 حجم: {last['volume']:.0f} (میانگین: {last['VOL_MA20']:.0f})
            """
            send_telegram_message(config.TELEGRAM_TOKEN, config.CHAT_ID, msg)
            logger.info(f"SELL سیگنال ارسال شد: {entry} | SL: {sl} | TP: {tp}")

    except Exception as e:
        logger.error(f"❌ خطای سیستم: {e}")

# اجرای یکباره (برای GitHub Actions)
if __name__ == "__main__":
    logger.info("🚀 سیستم سیگنال‌دهی راه‌اندازی شد (اجرای یکباره)")
    check_signal()  # فقط یکبار اجرا می‌شود
    logger.info("✅ سیستم به پایان رسید")
