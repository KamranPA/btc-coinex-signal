# main.py
import time
import schedule
from datetime import datetime, timezone, time as dt_time
import logging

from data_handler import fetch_kucoin_data
from strategy import generate_signal
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
        df = fetch_kucoin_data(config.SYMBOL, config.TIMEFRAME, limit=200)
        if df.empty or len(df) < 200:
            logger.warning("داده کافی موجود نیست")
            return

        signal = generate_signal(df)
        if signal and config.TELEGRAM_TOKEN and config.CHAT_ID:
            msg = f"""
🟢 <b>{signal['type']} سیگنال</b>
📌 نماد: {config.SYMBOL}
🕒 زمان: {df.index[-1]}
📊 ورود: {signal['entry']}
🛑 حد ضرر: {signal['sl']}
🎯 حد سود: {signal['tp']}
🧮 RSI: {signal['rsi']}
📈 حجم: {signal['volume_ratio']}x میانگین
            """
            send_telegram_message(config.TELEGRAM_TOKEN, config.CHAT_ID, msg)
            logger.info(f"{signal['type']} سیگنال ارسال شد: {signal['entry']}")

    except Exception as e:
        logger.error(f"❌ خطای سیستم: {e}")

if __name__ == "__main__":
    logger.info("🚀 سیستم سیگنال‌دهی راه‌اندازی شد (هر 1 ساعت)")
    check_signal()
    logger.info("✅ سیستم به پایان رسید")
