import requests
import json

def send_signal(signal):
    with open('config/settings.json') as f:
        config = json.load(f)
    
    token = config['telegram']['token']
    chat_id = config['telegram']['chat_id']

    message = (
        f"🟢 <b>{signal['action'].upper()} {signal['direction'].upper()}</b>\n"
        f"📌 ورود: {signal['entry']}\n"
        f"🎯 حد سود: {signal['tp']}\n"
        f"⛔ حد ضرر: {signal['sl']}\n"
        f"📊 نسبت: 1:{signal['risk_reward']}\n"
        f"🔍 دلیل: {signal['reason']}\n"
        f"🕒 {signal['time']}"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.get(url, params=data, timeout=10)
    except:
        pass
