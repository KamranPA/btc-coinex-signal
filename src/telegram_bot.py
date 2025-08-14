# src/telegram_bot.py
import requests
import logging
import config

logger = logging.getLogger(__name__)

def send_signal(signal_data):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.warning("⚠️ توکن یا Chat ID تنظیم نشده — ارسال سیگنال رد شد")
        return

    message = (
        f"🚀 سیگنال جدید {signal_data['symbol']} ({config.TIMEFRAME})\n"
        f"نوع: {'خرید' if signal_data['signal'] == 1 else 'فروش'}\n"
        f"ورود: {signal_data['entry']:.2f}\n"
        f"حد ضرر: {signal_data['sl']:.2f}\n"
        f"حد سود: {signal_data['tp']:.2f}\n"
        f"زمان: {signal_data['timestamp']}"
    )

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': config.TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }

    try:
        logger.debug(f"📤 ارسال سیگنال به تلگرام... Chat ID: {config.TELEGRAM_CHAT_ID}")
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info("✅ سیگنال با موفقیت به تلگرام ارسال شد")
        else:
            logger.error(f"❌ خطا در ارسال تلگرام: {response.status_code} | {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ اتصال به تلگرام ناموفق: {str(e)}", exc_info=True)
