# main.py
# Entry point for the RSI + Ichimoku backtesting system

import json
import os
import yaml
import logging
from datetime import datetime

# --- Setup Logger ---
def setup_logger():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(f"{log_dir}/bot.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()

# --- Load Backtest Config ---
def load_backtest_config():
    config_path = 'config/backtest_config.yml'
    if not os.path.exists(config_path):
        logger.error(f"❌ Config file not found at {config_path}")
        exit(1)
    with open(config_path, 'r', encoding='utf-8') as f:
        try:
            config = yaml.safe_load(f)
            logger.info("✅ Configuration loaded from backtest_config.yml")
            return config['backtest']
        except Exception as e:
            logger.error(f"❌ Failed to parse YAML config: {e}")
            exit(1)

# --- Load Settings (strategy parameters) ---
def load_settings():
    settings_path = 'config/settings.json'
    if not os.path.exists(settings_path):
        logger.error(f"❌ Settings file not found at {settings_path}")
        exit(1)
    with open(settings_path, 'r') as f:
        return json.load(f)

# --- Mock Data Loader (Replace with real CoinEx API later) ---
def load_data(symbol, timeframe):
    # در حالت واقعی، اینجا از CoinEx API استفاده کنید
    # برای تست، یک دیتافریم خالی با ستون‌های مورد نیاز بسازیم
    import pandas as pd
    import numpy as np

    # فقط برای شبیه‌سازی داده
    dates = pd.date_range(start='2023-01-01', periods=1000, freq='H')
    np.random.seed(42)
    close = 30000 + np.random.randn(1000).cumsum() * 10
    high = close * 1.01
    low = close * 0.99
    open_price = close[:-1].tolist() + [close[-1]]

    df = pd.DataFrame({
        'timestamp': dates,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'volume': np.random.randint(100, 1000, 1000)
    })
    df.set_index('timestamp', inplace=True)
    logger.info(f"📊 Generated mock data for {symbol} on {timeframe}")
    return df

# --- Mock Signal Generator ---
def generate_signals(df, settings):
    import pandas as pd
    # شبیه‌سازی سیگنال (در واقعیت از src.strategy استفاده کنید)
    df = df.copy()
    df['signal'] = 0
    # هر 100 شمع یک سیگنال صعودی
    df.loc[df.index[::100], 'signal'] = 1
    # هر 150 شمع یک سیگنال نزولی
    df.loc[df.index[75::150], 'signal'] = -1
    logger.info("✅ Mock signals generated (for testing)")
    return df

# --- Mock Backtester ---
def run_backtest(df):
    from collections import defaultdict
    trades = []
    position = None
    entry_idx = None
    win_count = 0
    total_trades = 0

    for i in range(len(df)):
        signal = df['signal'].iloc[i]
        price = df['close'].iloc[i]

        # ورود
        if signal == 1 and not position:
            entry_price = price
            stop_loss = price * 0.99
            take_profit = price * 1.03
            entry_idx = i
            position = 'long'

        elif signal == -1 and not position:
            entry_price = price
            stop_loss = price * 1.01
            take_profit = price * 0.97
            entry_idx = i
            position = 'short'

        # خروج
        if position == 'long':
            if df['low'].iloc[i] <= stop_loss:
                trades.append({'type': 'long', 'entry': entry_price, 'exit': stop_loss, 'success': False})
                total_trades += 1
                position = None
            elif df['high'].iloc[i] >= take_profit:
                trades.append({'type': 'long', 'entry': entry_price, 'exit': take_profit, 'success': True})
                total_trades += 1
                win_count += 1
                position = None

        elif position == 'short':
            if df['high'].iloc[i] >= stop_loss:
                trades.append({'type': 'short', 'entry': entry_price, 'exit': stop_loss, 'success': False})
                total_trades += 1
                position = None
            elif df['low'].iloc[i] <= take_profit:
                trades.append({'type': 'short', 'entry': entry_price, 'exit': take_profit, 'success': True})
                total_trades += 1
                win_count += 1
                position = None

    # گزارش
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    report = {
        "total_trades": total_trades,
        "successful_trades": win_count,
        "failed_trades": total_trades - win_count,
        "win_rate": round(win_rate, 2),
        "trades": trades,
        "start_time": str(df.index[0]),
        "end_time": str(df.index[-1]),
        "timestamp": datetime.now().isoformat()
    }

    # ذخیره نتایج
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    with open(f"{results_dir}/backtest_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    with open(f"{results_dir}/trades_log.csv", "w") as f:
        pd.DataFrame(trades).to_csv(f, index=False)

    logger.info(f"✅ Backtest completed: {total_trades} trades, {win_rate:.1f}% win rate")
    return report

# --- Send Report to Telegram ---
def send_telegram_report(report, secrets):
    try:
        import requests
        token = secrets['telegram']['bot_token']
        chat_id = secrets['telegram']['chat_id']
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        total = report['total_trades']
        wins = report['successful_trades']
        fails = report['failed_trades']
        win_rate = report['win_rate']

        message = f"""
📊 *Backtest Results - RSI+Ichimoku*

📈 Total Trades: {total}
✅ Successful: {wins}
❌ Failed: {fails}
🎯 Win Rate: {win_rate}%

🔍 *Trade Details*:
"""
        for trade in report['trades'][:5]:
            status = "✅ Success" if trade['success'] else "❌ Failed"
            message += f"\n{status} | {trade['type'].title()}\n"
            message += f"💰 Entry: {trade['entry']:.2f} → Exit: {trade['exit']:.2f}\n"

        if len(report['trades']) > 5:
            message += f"\n... and {len(report['trades']) - 5} more."

        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        requests.post(url, data=payload, timeout=10)
        logger.info("📤 Telegram report sent successfully")
    except Exception as e:
        logger.error(f"❌ Failed to send Telegram message: {e}")

# --- Main Execution ---
def main():
    logger.info("🚀 Starting automated backtest...")

    # 1. بارگذاری تنظیمات
    bt_config = load_backtest_config()
    settings = load_settings()

    # 2. بارگذاری داده
    logger.info(f"📥 Loading data for {bt_config['symbol']} on {bt_config['timeframe']}...")
    df = load_data(bt_config['symbol'], bt_config['timeframe'])

    # 3. تولید سیگنال
    df = generate_signals(df, settings)

    # 4. اجرای بکتست
    report = run_backtest(df)

    # 5. ارسال به تلگرام (اگر تنظیمات وجود داشته باشد)
    if os.path.exists('config/secrets.json'):
        try:
            with open('config/secrets.json', 'r') as f:
                secrets = json.load(f)
            if 'telegram' in secrets and secrets['telegram']['bot_token']:
                send_telegram_report(report, secrets)
        except Exception as e:
            logger.error(f"Telegram setup failed: {e}")
    else:
        logger.warning("No secrets.json found. Skipping Telegram.")

    logger.info("🎉 Backtest workflow completed successfully.")

if __name__ == "__main__":
    main()
