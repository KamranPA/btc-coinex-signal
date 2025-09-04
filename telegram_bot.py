# telegram_bot.py
import telegram
from telegram import ParseMode
import pandas as pd

async def send_report(trades_df, summary, config):
    bot = telegram.Bot(token=config.TELEGRAM_TOKEN)
    
    # خلاصه گزارش
    message = f"""
📊 *بک‌تست اندیکاتور Mutanabby_AI | Fresh Algo V24*
📌 نماد: `{config.SYMBOL}`
🕒 تایم‌فریم: `{config.TIMEFRAME}`
📅 بازه: `{config.START_DATE} → {config.END_DATE}`

🔢 تعداد معاملات: `{len(trades_df)}`
✅ تعداد سود: `{len(trades_df[trades_df['pnl'] > 0])}`
❌ تعداد ضرر: `{len(trades_df[trades_df['pnl'] < 0])}`
📈 نرخ موفقیت: `{summary['win_rate']:.2f}%`
📉 ماکزیمم Drawdown: `{summary['max_drawdown']:.2f}%`
    """
    
    await bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=message, parse_mode=ParseMode.MARKDOWN)

    # جزئیات معاملات
    for idx, row in trades_df.iterrows():
        detail = f"""
🔁 معامله #{idx+1}
📅 {row['entry_time']}
🟢 {row['type'].upper()} | قیمت ورود: `{row['entry_price']:.2f}`
🎯 TP1: `{row['tp1']:.2f}` | TP2: `{row['tp2']:.2f}` | TP3: `{row['tp3']:.2f}`
💰 سود/ضرر: `{row['pnl']:.2f}%`
        """
        await bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=detail, parse_mode=ParseMode.MARKDOWN)
