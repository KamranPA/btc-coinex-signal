# main.py
import os
from data_fetcher import fetch_ohlcv
from divergence_detector import DivergenceDetector
from telegram_notifier import send_telegram_message

def main():
    # تنظیمات از متغیرهای محیطی (GitHub Secrets)
    symbol = os.getenv("SYMBOL", "BTC/USDT")
    timeframe = os.getenv("TIMEFRAME", "1h")
    limit = int(os.getenv("LIMIT", "500"))

    print(f"🔍 Fetching {symbol} data on {timeframe}...")

    df = fetch_ohlcv(symbol, timeframe, limit)
    detector = DivergenceDetector(df)
    signals = detector.detect()

    if not signals:
        print("📭 No divergence signals found.")
        return

    for sig in signals:
        message = (
            f"<b>📊 RSI Momentum Divergence Detected!</b>\n"
            f"• Type: {sig['type']} 📈\n"
            f"• Direction: {sig['direction']}\n"
            f"• Symbol: {symbol}\n"
            f"• Timeframe: {timeframe}\n"
            f"• Time: {sig['timestamp']}\n"
            f"• Price: ${sig['price']:.2f}\n"
            f"• RSI: {sig['rsi']:.2f}"
        )
        print(message)
        send_telegram_message(message)

if __name__ == "__main__":
    main()
