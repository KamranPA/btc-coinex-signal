import requests
import os
import json
from datetime import datetime

def send_workflow_status():
    """ارسال وضعیت workflow به تلگرام"""
    
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not telegram_token or not chat_id:
        print("Telegram credentials not found")
        return
    
    # اطلاعات workflow از محیط
    workflow_name = os.getenv('GITHUB_WORKFLOW', 'Unknown')
    run_id = os.getenv('GITHUB_RUN_ID', 'Unknown')
    repository = os.getenv('GITHUB_REPOSITORY', 'Unknown')
    status = os.getenv('JOB_STATUS', 'completed')
    
    # ایجاد پیام
    message = f"""
🔄 <b>Workflow Status Update</b>

📊 <b>Workflow:</b> {workflow_name}
🏷️ <b>Run ID:</b> #{run_id}
📁 <b>Repository:</b> {repository}
⏰ <b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ <b>Status:</b> {status.capitalize()}

🔗 <a href="https://github.com/{repository}/actions/runs/{run_id}">View Workflow Run</a>
    """
    
    # ارسال به تلگرام
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': True
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Workflow status sent to Telegram")
        else:
            print(f"Failed to send status: {response.text}")
    except Exception as e:
        print(f"Error sending workflow status: {e}")

if __name__ == "__main__":
    send_workflow_status()
