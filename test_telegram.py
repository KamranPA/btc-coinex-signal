# test_telegram.py
import os
import requests
import logging

# تنظیم لاگ
logging.basicConfig(level=logging.INFO, format='%(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            logger.info("✅ پیام به تلگرام با موفقیت ارسال شد.")
            return True
        else:
            logger.error(f"❌ خطا در ارسال تلگرام: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ ارتباط با تلگرام ناموفق: {e}")
        return False

def main():
    logger.info("🚀 شروع تست ارسال تلگرام از طریق GitHub Secrets")

    # خواندن از محیط (از secrets)
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("CHAT_ID")

    if not token:
        logger.error("❌ TELEGRAM_TOKEN یافت نشد! مطمئن شوید در Secrets تنظیم شده باشد.")
        return
    if not chat_id:
        logger.error("❌ CHAT_ID یافت نشد! مطمئن شوید در Secrets تنظیم شده باشد.")
        return

    logger.info(f"✅ توکن و چت آی‌دی بارگذاری شد (چت آی‌دی: {chat_id})")

    # ارسال پیام تست
    msg = """
🧪 <b>تست ارسال تلگرام</b>
✅ سیستم ارسال پیام فعال است
📅 {}
⏱️ این پیام از طریق GitHub Actions ارسال شد
""".format(__import__('datetime').datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    success = send_telegram_message(token, chat_id, msg)

    if success:
        logger.info("🎉 تست موفقیت‌آمیز بود!")
    else:
        logger.error("💣 تست با شکست مواجه شد.")

if __name__ == "__main__":
    main()
