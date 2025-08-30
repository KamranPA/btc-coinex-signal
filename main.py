# main.py
import os
import sys
import pandas as pd
from datetime import datetime
from utils.logger_config import logger
from data_fetcher import fetch_ohlcv
from divergence_detector import DivergenceDetector
from telegram_notifier import send_telegram_message

def main():
    try:
        # تنظیمات از متغیرهای محیطی
        symbol = os.getenv("SYMBOL", "BTC/USDT")
        timeframe = os.getenv("TIMEFRAME", "1h")
        limit = int(os.getenv("LIMIT", "500"))
        start_date_str = os.getenv("START_DATE", None)
        end_date_str = os.getenv("END_DATE", None)

        logger.info("=" * 60)
        logger.info("🚀 RSI MOMENTUM DIVERGENCE BOT (CoinEx - Public API)")
        logger.info(f"⚙️  SYMBOL={symbol}")
        logger.info(f"📊 TIMEFRAME={timeframe}")
        logger.info(f"🔢 LIMIT={limit}")
        logger.info(f"📅 START_DATE={start_date_str or 'Unset'}")
        logger.info(f"📅 END_DATE={end_date_str or 'Unset'}")
        logger.info("=" * 60)

        # مرحله ۱: دریافت داده
        df = fetch_ohlcv(symbol, timeframe, limit)
        if df.empty:
            logger.critical("🛑 No data received. Exiting.")
            sys.exit(1)

        # مرحله ۲: فیلتر داده بر اساس بازه زمانی
        if start_date_str or end_date_str:
            try:
                # تبدیل تاریخ‌ها به Timestamp و تضمین UTC
                if start_date_str:
                    start_date = pd.to_datetime(start_date_str).tz_localize('UTC') if pd.to_datetime(start_date_str).tzinfo is None else pd.to_datetime(start_date_str)
                    df = df[df.index >= start_date]
                    logger.info(f"✂️  Filtered: keep data >= {start_date}")

                if end_date_str:
                    end_date = pd.to_datetime(end_date_str).tz_localize('UTC') if pd.to_datetime(end_date_str).tzinfo is None else pd.to_datetime(end_date_str)
                    df = df[df.index <= end_date]
                    logger.info(f"✂️  Filtered: keep data <= {end_date}")

                if df.empty:
                    logger.warning("📭 No data remains after date filtering.")
                    sys.exit(0)

                logger.info(f"📊 Final data range after filtering: {df.index[0]} to {df.index[-1]}")

            except Exception as e:
                logger.error(f"❌ Error parsing or applying date range: {e}")
                sys.exit(1)

        # مرحله ۳: تشخیص واگرایی
        detector = DivergenceDetector(df)
        signals = detector.detect()

        if not signals:
            logger.info("📭 No divergence signals found within the specified time range.")
            return

        # مرحله ۴: ارسال سیگنال به تلگرام
        for sig in signals:
            message = (
                f"<b>🎯 RSI Momentum Divergence Detected!</b>\n"
                f"• Type: <b>{sig['type']}</b> {'🟢📈' if sig['type'] == 'Bullish' else '🔴📉'}\n"
                f"• Direction: <i>{sig['direction']}</i>\n"
                f"• Symbol: <code>{symbol}</code>\n"
                f"• Timeframe: <code>{timeframe}</code>\n"
                f"• Time (UTC): <code>{sig['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</code>\n"
                f"• Price: <code>${sig['price']:.6f}</code>\n"
                f"• RSI: <code>{sig['rsi']:.2f}</code>"
            )
            logger.info(f"📤 Sending signal: {sig['type']} at {sig['timestamp']}")
            success = send_telegram_message(message)
            if not success:
                logger.error("Failed to send signal to Telegram.")

    except Exception as e:
        logger.exception("💥 CRITICAL ERROR in main execution")
        sys.exit(1)

if __name__ == "__main__":
    main()
