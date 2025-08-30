# main.py
import os
import sys
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

        logger.info("="*60)
        logger.info("🚀 RSI MOMENTUM DIVERGENCE BOT (CoinEx - Public API)")
        logger.info(f"⚙️  SYMBOL={symbol}, TIMEFRAME={timeframe}, LIMIT={limit}")
        logger.info("🔓 Using public API — no authentication required.")
        logger.info("="*60)

        # مرحله ۱: دریافت داده (بدون API Key)
        df = fetch_ohlcv(symbol, timeframe, limit)
        if df.empty:
            logger.critical("🛑 No data received. Exiting.")
            sys.exit(1)

        # مرحله ۲: تشخیص واگرایی
        detector = DivergenceDetector(df)
        signals = detector.detect()

        if not signals:
            logger.info("📭 No divergence signals found. Run complete.")
            return

        # مرحله ۳: ارسال سیگنال
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
            send_telegram_message(message)

    except Exception as e:
        logger.exception("💥 CRITICAL ERROR in main execution")
        sys.exit(1)

if __name__ == "__main__":
    main()
