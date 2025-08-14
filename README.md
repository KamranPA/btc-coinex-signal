# Bitcoin Institutional Trading System

This system generates trading signals based on institutional trading strategies for Bitcoin on a 15-minute timeframe.

## Features
- Multi-exchange support (KuCoin, Binance, Bybit)
- Advanced institutional strategy with 5 filters
- Daily performance reports
- Backtesting with historical data
- GitHub Actions integration

## How to Run Backtests

1. Manual Trigger:
   - Go to GitHub Actions
   - Select "Run Backtest" workflow
   - Set start and end dates (default: 2023-01-01 to 2023-12-31)
   - Click "Run workflow"

2. Scheduled Runs:
   - Daily at 00:00 UTC

## Results
Backtest results are available as artifacts:
1. Daily reports in text format
2. Equity curve charts
3. Filter activation charts

## Strategy Parameters
```python
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
```
