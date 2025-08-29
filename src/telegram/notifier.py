import requests
import json

def send_telegram_report(report, secrets):
    token = secrets['telegram']['bot_token']
    chat_id = secrets['telegram']['chat_id']
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    message = f"""
📊 *نتایج بکتست*

📈 تعداد معاملات: {report['total_trades']}
✅ معاملات موفق: {report['successful_trades']}
❌ معاملات شکست: {report['failed_trades']}
🎯 وین ریت: {report['win_rate']}%
📉 ماکس دردراون: {report['max_drawdown']}%

📌 *جزئیات معاملات*:
"""
    for trade in report['trades']:
        status = "✅ موفق" if trade['success'] else "❌ شکست"
        message += f"\n{status}\n"
        message += f"ورود: {trade['entry']:.4f} | حد سود: {trade['tp']:.4f} | حد ضرر: {trade['sl']:.4f}\n"

    payload = {'chat_id': chat_id, 'text': message, 'parse_mode': 'Markdown'}
    requests.post(url, data=payload)
