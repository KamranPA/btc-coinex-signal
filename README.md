# RSI Momentum + Ichimoku Algorithmic Trading Bot

A backtestable trading system for cryptocurrencies based on **RSI Momentum Divergence** and **Ichimoku Kinko Hyo** confirmation.

## 📌 Features
- Backtesting on 1h timeframe
- Divergence detection (RSI on momentum)
- Ichimoku confirmation
- Market regime detection (Trending vs Ranging)
- Telegram reporting
- Modular & debuggable structure
- Ready for future live trading (CoinEx)

## 🔐 Setup
1. `cp config/secrets.json.example config/secrets.json`
2. Fill in your CoinEx and Telegram credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python main.py`

## 📂 Structure
- `/src/indicators`: Core logic
- `/src/strategy`: Signal combination
- `/src/backtest`: Manual backtest engine
- `/src/telegram`: Telegram alerts
- `/results`: Output reports

## 📄 License
Mozilla Public License 2.0 (MPL 2.0) - See LICENSE.
