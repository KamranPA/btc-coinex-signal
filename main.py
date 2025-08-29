# main.py
# RSI Momentum + Ichimoku Backtesting System for Cryptocurrencies
# Powered by CoinEx API and GitHub Actions
# Sends results to Telegram via GitHub Secrets

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

# --- Load Real Data from CoinEx API ---
def load_data_from_coinex(symbol="BTC-USDT", timeframe="1h", limit=1000):
    """
    Fetch real OHLCV data from CoinEx API
    """
    url = "https://api.coinex.com/v1/market/kline"
    params = {
        'market': symbol.replace('-', ''),
        'type': timeframe,
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

# --- Calculate Ichimoku Kinko Hyo ---
def calculate_ichimoku(df, tenkan=9, kijun=26, senkou=52):
    high_tenkan = df['high'].rolling(tenkan).max()
    low_tenkan = df['low'].rolling(tenkan).min()
    df['tenkan_sen'] = (high_tenkan + low_tenkan) / 2

    high_kijun = df['high'].rolling(kijun).max()
    low_kijun = df['low'].rolling(kijun).min()
    df['kijun_sen'] = (high_kijun + low_kijun) / 2

    df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(kijun)
    df['senkou_span_b'] = df['low'].rolling(senkou).min().rolling(senkou).mean().shift(kijun)
    df['chikou_span'] = df['close'].shift(-kijun)

    return df

# --- Detect RSI Momentum Divergence ---
def detect_rsi_momentum_divergence(df, rsi_length=14, momentum_period=10, lookback=5):
    df['momentum'] = df['close'].diff(momentum_period)
    df['rsi'] = ta.momentum.RSIIndicator(df['momentum'], window=rsi_length).rsi()

    def is_pivot_low(series, i, lb=lookback):
        return all(series[i] < series[i-j] for j in range(1, lb+1)) and \
               all(series[i] < series[i+j] for j in range(1, lb+1))

    def is_pivot_high(series, i, lb=lookback):
        return all(series[i] > series[i-j] for j in range(1, lb+1)) and \
               all(series[i] > series[i+j] for j in range(1, lb+1))

    bullish_div = []
    bearish_div = []

    for i in range(lookback, len(df) - lookback):
        # Bullish Divergence: Price lower low, RSI higher low
        if is_pivot_low(df['low'], i) and is_pivot_low(df['rsi'], i):
            if df['low'].iloc[i] < df['low'].iloc[i-lookback] and df['rsi'].iloc[i] > df['rsi'].iloc[i-lookback]:
                bullish_div.append(i)

        # Bearish Divergence: Price higher high, RSI lower high
        if is_pivot_high(df['high'], i) and is_pivot_high(df['rsi'], i):
            if df['high'].iloc[i] > df['high'].iloc[i-lookback] and df['rsi'].iloc[i] < df['rsi'].iloc[i-lookback]:
                bearish_div.append(i)

    return bullish_div, bearish_div

# --- Generate Signals ---
def generate_signals(df, settings):
    df = calculate_ichimoku(df)
    bullish_div, bearish_div = detect_rsi_momentum_divergence(df, settings['rsi_length'])

    df['signal'] = 0

    # Confirm bullish signal with Ichimoku
    for idx in bullish_div:
        if df['close'].iloc[idx] > max(df['senkou_span_a'].iloc[idx], df['senkou_span_b'].iloc[idx]) and \
           df['tenkan_sen'].iloc[idx] > df['kijun_sen'].iloc[idx]:
            df['signal'].iloc[idx] = 1

    # Confirm bearish signal with Ichimoku
    for idx in bearish_div:
        if df['close'].iloc[idx] < min(df['senkou_span_a'].iloc[idx], df['senkou_span_b'].iloc[idx]) and \
           df['tenkan_sen'].iloc[idx] < df['kijun_sen'].iloc[idx]:
            df['signal'].iloc[idx] = -1

    logger.info("✅ Signals generated using RSI Momentum + Ichimoku")
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
                trades.append({'type': 'long', 'entry': entry_price, 'exit': stop_loss, 'success': False})
                total_trades += 1
                position = None
            elif df['high'].iloc[i] >= take_profit:
                profit = (take_profit - entry_price) / entry_price * 100
                trades.append({'type': 'long', 'entry': entry_price, 'exit': take_profit, 'success': True, 'profit_pct': profit})
                total_trades += 1
                win_count += 1
                position = None

        # Exit Short
        elif position == 'short':
            if df['high'].iloc[i] >= stop_loss:
                trades.append({'type': 'short', 'entry': entry_price, 'exit': stop_loss, 'success': False})
                total_trades += 1
                position = None
            elif df['low'].iloc[i] <= take_profit:
                profit = (entry_price - take_profit) / entry_price * 100
                trades.append({'type': 'short', 'entry': entry_price, 'exit': take_profit, 'success': True, 'profit_pct': profit})
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
def send_telegram_report(report):
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

        message = f"""
📊 *Backtest Results - RSI+Ichimoku*

📈 Total Trades: {total}
✅ Successful: {wins}
❌ Failed: {fails}
🎯 Win Rate: {win_rate}%
💰 Total Profit: {profit}%

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
        response = requests.post(url, data=payload, timeout=10)
        if response.status_code == 200:
            logger.info("📤 Telegram report sent successfully!")
        else:
            logger.error(f"❌ Telegram send failed: {response.text}")
    except KeyError as e:
        logger.warning(f"⚠️ Telegram skipped: {e} not found. Make sure GitHub Secrets are set correctly.")
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

    # Generate signals
    try:
        import ta
        df = generate_signals(df, settings)
    except Exception as e:
        logger.error(f"❌ Signal generation failed: {e}")
        exit(1)

    # Run backtest
    report = run_backtest(df, settings)

    # Send to Telegram (if secrets are set)
    if 'TELEGRAM_BOT_TOKEN' in os.environ and 'TELEGRAM_CHAT_ID' in os.environ:
        send_telegram_report(report)
    else:
        logger.warning("⚠️ Telegram skipped: Environment variables not set. Check GitHub Secrets.")

    logger.info("🎉 Backtest workflow completed successfully.")

if __name__ == "__main__":
    main()
