import requests
import json

def send_signal(signal):
    with open('config/settings.json') as f:
        config = json.load(f)
    token = config['telegram']['token']
    chat_id = config['telegram']['chat_id']

    message = (
        f"🟢 <b>سیگنال خرید BTC/USDT</b>\n"
        f"📌 ورود: {signal['entry']}\n"
        f"🎯 TP: {signal['tp']}\n"
        f"⛔ SL: {signal['sl']}\n"
        f"📊 R:R = 1:{signal['risk_reward']}\n"
        f"⚡ تأیید: {sum(1 for v in signal['filters'].values() if v)}/6 فیلتر\n"
        f"🕒 {signal['time']}"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
    try:
        requests.get(url, data=data, timeout=10)
    except:
        pass
