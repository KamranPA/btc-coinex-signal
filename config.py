# config.py
import os

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

SYMBOL = "BTC-USDT"
TIMEFRAME = "15min"
EXCHANGES = ["kucoin", "binance"]  # ✅ Bybit حذف شد

STRATEGY_PARAMS = {
    "short_ema": 20,
    "long_ema": 50,
    "rsi_period": 14,
    "rsi_buy": 40,
    "rsi_sell": 60,
    "vol_lookback": 50,
    "vol_std_mult": 3,
    "atr_mult_sl": 0.5,
    "atr_mult_tp": 3
}
