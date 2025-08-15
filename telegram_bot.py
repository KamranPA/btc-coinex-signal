# telegram_bot.py
import requests
import json

def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"⚠️ خطای ارسال تلگرام: {response.text}")
    except Exception as e:
        print(f"❌ خطا در اتصال تلگرام: {e}")
