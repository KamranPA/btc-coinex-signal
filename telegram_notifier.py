# telegram_notifier.py
import requests
import os
from utils.logger_config import logger

def send_telegram_message(message: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        logger.critical("🚨 TELEGRAM_BOT_TOKEN is missing. Cannot send message.")
        return False
    if not chat_id:
        logger.critical("🚨 TELEGRAM_CHAT_ID is missing. Cannot send message.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    try:
        logger.debug("📤 Sending signal to Telegram...")
        response = requests.post(url, data=payload, timeout=15)
        if response.status_code == 200:
            logger.info("✅ Signal successfully sent to Telegram.")
            return True
        else:
            logger.error(f"❌ Telegram API error: {response.status_code} | {response.text}")
            return False
    except requests.exceptions.Timeout:
        logger.error("⏰ Telegram request timed out.")
    except requests.exceptions.ConnectionError:
        logger.error("🔌 Failed to connect to Telegram API.")
    except Exception as e:
        logger.exception(f"💥 Unexpected error sending to Telegram: {e}")
    return False
