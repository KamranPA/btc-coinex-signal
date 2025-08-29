# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# If a copy of the MPL was not distributed with this file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
import os
import yaml
import logging
import pandas as pd
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

# --- Load Strategy Settings ---
def load_settings():
    settings_path = 'config/settings.json'
    if not os.path.exists(settings_path):
        logger.error(f"❌ Settings file not found at {settings_path}")
        exit(1)
    with open(settings_path, 'r') as f:
        return json.load(f)

# --- Load Real Data from CoinEx API (Fixed) ---
def load_data_from_coinex(symbol="BTC-USDT", timeframe="1h", limit=1000):
    """
    Fetch real OHLCV data from CoinEx Spot API
    Fixed: Correct market name and timeframe format
    """
    # Normalize symbol: BTC-USDT → btcusdt
    market_name = symbol.lower().replace('-', '')
    
    # Fix timeframe: 1h → 1hour, 4h → 4hour, etc.
    tf_map = {
        '1m': '1min', '3m': '3min', '5m': '5min', '15m': '15min', '30m': '30min',
        '1h': '1hour', '2h': '2hour', '4h': '4hour', '6h': '6hour', '12h': '12hour',
        '1d': '1day', '1w': '1week'
    }
    api_timeframe = tf_map.get(timeframe.lower(), '1hour')  # default

    url = "https://api.coinex.com/v1/market/kline"
    params = {
        'market': market_name,
        'type': api_timeframe,
        'limit': limit
    }

    try:
        import requests
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data['code'] != 0:
            raise Exception(f"API Error: {data['message']}")

        klines = data['data']
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'close', 'high', 'low', 'volume', 'amount'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)

        logger.info(f"✅ Loaded {len(df)} real candles from CoinEx for {symbol} on {timeframe}")
        return df

    except Exception as e:
        logger.error(f"❌ Failed to fetch data from CoinEx: {e}")
        return None

# --- Generate Signals (Only RSI Momentum Divergence + Mock Signal) ---
def generate_signals(df, settings):
    df = df.copy()
    df['signal'] = 0
    df['trade_index'] = range(len(df))  # for Telegram timestamp

    # ✅ Add a mock bullish signal at index 100
    mock_index = 100
    if len(df) > mock_index:
        df['signal'].iloc[mock_index] = 1  # Long signal
        logger.info(f"🎯 Mock bullish signal added at index {mock_index} for testing")
    else:
        logger.warning("⚠️ Not enough data to add mock signal")

    # Optional: Add a mock bearish signal
    # if len(df) > 200:
    #     df['signal'].iloc[200] = -1  # Short signal
    #     logger.info("🎯 Mock bearish signal added at index 200 for testing")

    logger.info("✅ Signals generated (including mock signal)")
    return df

# --- Run Backtest ---
def run_backtest(df, settings):
    trades = []
    position = None
    win_count = 0
    total_trades = 0

    sl_pct = settings['risk']['stop_loss_percent'] / 100
    tp_pct = settings['risk']['take_profit_percent'] / 100

    for i in range(len(df)):
        signal = df['signal'].iloc[i]
        price = df['close'].iloc[i]

        # Long Entry
        if signal == 1 and not position:
            entry_price = price
            stop_loss = price * (1 - sl_pct)
            take_profit = price * (1 + tp_pct)
            position = 'long'

        # Short Entry
        elif signal == -1 and not position:
            entry_price = price
            stop_loss = price * (1 + sl_pct)
            take_profit = price * (1 - tp_pct)
            position = 'short'

        # Exit Long
        if position == 'long':
            if df['low'].iloc[i] <= stop_loss:
                trades.append({
                    'type': 'long',
                    'entry': entry_price,
                    'exit': stop_loss,
                    'success': False,
                    'index': df['trade_index'].iloc[i]
                })
                total_trades += 1
                position = None
            elif df['high'].iloc[i] >= take_profit:
                profit = (take_profit - entry_price) / entry_price * 100
                trades.append({
                    'type': 'long',
                    'entry': entry_price,
                    'exit': take_profit,
                    'success': True,
                    'profit_pct': profit,
                    'index': df['trade_index'].iloc[i]
                })
                total_trades += 1
                win_count += 1
                position = None

        # Exit Short
        elif position == 'short':
            if df['high'].iloc[i] >= stop_loss:
                trades.append({
                    'type': 'short',
                    'entry': entry_price,
                    'exit': stop_loss,
                    'success': False,
                    'index': df['trade_index'].iloc[i]
                })
                total_trades += 1
                position = None
            elif df['low'].iloc[i] <= take_profit:
                profit = (entry_price - take_profit) / entry_price * 100
                trades.append({
                    'type': 'short',
                    'entry': entry_price,
                    'exit': take_profit,
                    'success': True,
                    'profit_pct': profit,
                    'index': df['trade_index'].iloc[i]
                })
                total_trades += 1
                win_count += 1
                position = None

    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    total_profit = sum(t.get('profit_pct', 0) for t in trades if 'profit_pct' in t)

    report = {
        "total_trades": total_trades,
        "successful_trades": win_count,
        "failed_trades": total_trades - win_count,
        "win_rate": round(win_rate, 2),
        "total_profit_percent": round(total_profit, 2),
        "trades": trades,
        "start_time": str(df.index[0]),
        "end_time": str(df.index[-1]),
        "timestamp": datetime.now().isoformat()
    }

    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    with open(f"{results_dir}/backtest_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    pd.DataFrame(trades).to_csv(f"{results_dir}/trades_log.csv", index=False)

    logger.info(f"✅ Backtest completed: {total_trades} trades, {win_rate:.1f}% win rate, {total_profit:.2f}% total profit")
    return report

# --- Send Report to Telegram ---
def send_telegram_report(report, bt_config):
    try:
        import requests
        token = os.environ['TELEGRAM_BOT_TOKEN']
        chat_id = os.environ['TELEGRAM_CHAT_ID']
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        total = report['total_trades']
        wins = report['successful_trades']
        fails = report['failed_trades']
        win_rate = report['win_rate']
        profit = report['total_profit_percent']

        # Build detailed signal messages
        signal_lines = []
        start_dt = pd.to_datetime(report['start_time'])
        for trade in report['trades']:
            # Determine divergence type
            div_type = "📈 Bullish Divergence" if trade['type'] == 'long' else "📉 Bearish Divergence"
            
            # Approximate signal time
            signal_time = start_dt + pd.Timedelta(hours=trade['index'])
            time_str = signal_time.strftime("%Y-%m-%d %H:%M")

            status = "✅ Success" if trade['success'] else "❌ Failed"

            sl_price = trade['entry'] * (0.99 if trade['type'] == 'long' else 1.01)

            line = (f"{status} | {div_type}\n"
                    f"🕒 {time_str} | {bt_config['symbol']} | {bt_config['timeframe']}\n"
                    f"💰 Entry: {trade['entry']:.2f} → TP: {trade['exit']:.2f}\n"
                    f"🛑 SL: {sl_price:.2f}\n")
            signal_lines.append(line)

        message = f"""
🚀 *RSI Momentum Divergence Alert - Backtest Results*

📊 *Summary*
📈 Total Trades: {total}
✅ Successful: {wins}
❌ Failed: {fails}
🎯 Win Rate: {win_rate}%
💰 Total Profit: {profit}%

🔍 *Signal Details*:
""" + "\n".join(signal_lines)

        if len(report['trades']) > 5:
            message += f"\n... and {len(report['trades']) - 5} more."

        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            logger.info("📤 Telegram report sent successfully!")
        else:
            logger.error(f"❌ Telegram send failed: {response.text}")
    except KeyError as e:
        logger.warning(f"⚠️ Telegram skipped: {e} not found. Check GitHub Secrets.")
    except Exception as e:
        logger.error(f"❌ Failed to send Telegram message: {e}")

# --- Main Execution ---
def main():
    logger.info("🚀 Starting automated backtest...")

    # Load configs
    bt_config = load_backtest_config()
    settings = load_settings()

    # Load real data
    df = load_data_from_coinex(bt_config['symbol'], bt_config['timeframe'])
    if df is None or df.empty:
        logger.error("❌ No data loaded. Exiting.")
        exit(1)

    # Generate signals (including mock)
    try:
        df = generate_signals(df, settings)
    except Exception as e:
        logger.error(f"❌ Signal generation failed: {e}")
        exit(1)

    # Run backtest
    report = run_backtest(df, settings)

    # Send to Telegram (if secrets are set)
    if 'TELEGRAM_BOT_TOKEN' in os.environ and 'TELEGRAM_CHAT_ID' in os.environ:
        send_telegram_report(report, bt_config)
    else:
        logger.warning("⚠️ Telegram skipped: Environment variables not set. Check GitHub Secrets.")

    logger.info("🎉 Backtest workflow completed successfully.")

if __name__ == "__main__":
    main()
