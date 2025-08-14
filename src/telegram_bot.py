import requests
import config

def send_signal(signal_data):
‎    # فقط اگر توکن تنظیم شده باشد ارسال می‌کند
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("Telegram credentials not set. Skipping send.")
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
        'text': message
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Telegram response: {response.status_code}")
    except Exception as e:
        print(f"Failed to send Telegram message: {str(e)}")
