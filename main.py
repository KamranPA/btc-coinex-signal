# main.py
import pandas as pd
import asyncio
from datetime import datetime
from coinex_api import fetch_data
from strategy import apply_strategy
from telegram_bot import send_report
import config

def calculate_risk_management(df):
    trades = []
    position = None
    entry_price = None
    tp1, tp2, tp3 = None, None, None

    for i, row in df.iterrows():
        if pd.isna(row['ema150']) or pd.isna(row['ema250']):
            continue

        # باز کردن معامله خرید
        if row['bull_signal'] and position != 'long':
            position = 'long'
            entry_price = row['close']
            risk = abs(entry_price - row['supertrend'])  # حد ضرر
            tp1 = entry_price + risk * 1
            tp2 = entry_price + risk * 2
            tp3 = entry_price + risk * 3
            trades.append({
                'entry_time': i,
                'type': 'buy',
                'entry_price': entry_price,
                'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                'pnl': None
            })

        # باز کردن معامله فروش
        elif row['bear_signal'] and position != 'short':
            position = 'short'
            entry_price = row['close']
            risk = abs(entry_price - row['supertrend'])
            tp1 = entry_price - risk * 1
            tp2 = entry_price - risk * 2
            tp3 = entry_price - risk * 3
            trades.append({
                'entry_time': i,
                'type': 'sell',
                'entry_price': entry_price,
                'tp1': tp1, 'tp2': tp2, 'tp3': tp3,
                'pnl': None
            })

    return pd.DataFrame(trades)

def calculate_summary(trades_df, df):
    wins = len(trades_df[trades_df['pnl'] > 0])
    losses = len(trades_df[trades_df['pnl'] < 0])
    win_rate = (wins / (wins + losses)) * 100 if wins + losses > 0 else 0

    # Drawdown ساده (اختلاف بین دو اوج)
    equity_curve = df['close'].pct_change().cumsum()
    running_max = equity_curve.cummax()
    drawdown = (equity_curve - running_max).min() * 100

    return {
        'total_trades': len(trades_df),
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'max_drawdown': abs(drawdown)
    }

async def main():
    print("دریافت داده از CoinEx...")
    df = fetch_data()
    print(f"داده‌ها دریافت شد: {len(df)} کندل")

    print("اعمال استراتژی...")
    df = apply_strategy(df, config)

    print("محاسبه معاملات...")
    trades_df = calculate_risk_management(df)

    print("محاسبه خلاصه...")
    summary = calculate_summary(trades_df, df)

    print("ارسال گزارش به تلگرام...")
    await send_report(trades_df, summary, config)

    # ذخیره معاملات
    trades_df.to_csv("results/trades.csv", index=False)
    print("بک‌تست کامل شد. نتایج در results/trades.csv ذخیره شد.")

if __name__ == "__main__":
    asyncio.run(main())
