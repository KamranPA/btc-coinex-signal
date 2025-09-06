import requests
from config.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, text):
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending message to Telegram: {e}")
            return False
    
    def format_signal_message(self, symbol, signal_type, entry, sl, tp1, tp2, tp3):
        message = f"""
🚀 <b>سیگنال معاملاتی جدید</b> 🚀

📊 <b>نماد:</b> {symbol}
🎯 <b>نوع سیگنال:</b> {signal_type}
💰 <b>ورود:</b> {entry}

📉 <b>حد ضرر (SL):</b> {sl}
📈 <b>حد سود ۱ (TP1):</b> {tp1}
📈 <b>حد سود ۲ (TP2):</b> {tp2}
📈 <b>حد سود ۳ (TP3):</b> {tp3}

⚖️ <b>ریسک به ریوارد:</b> ۱:۳
⏰ <b>تایم فریم:</b> ۱۵ دقیقه

⚠️ <i>این یک سیگنال اتوماتیک است. مسئولیت معاملات بر عهده خودتان است.</i>
        """
        return message
