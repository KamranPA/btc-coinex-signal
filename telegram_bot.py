# telegram_bot.py

from telegram import Bot
from telegram.constants import ParseMode
import asyncio
import pandas as pd
import numpy as np

async def send_report(trades_df, summary, config):
    """
    ارسال گزارش بک‌تست به ربات تلگرام
    """

    bot = Bot(token=config.TELEGRAM_TOKEN)

    # خلاصه گزارش
    message = f"""
📊 <b>بک‌تست اندیکاتور Mutanabby_AI | Fresh Algo V24</b>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 <b>نماد:</b> <code>{config.SYMBOL}</code>
🕒 <b>تایم‌فریم:</b> <code>{config.TIMEFRAME}</code>
📅 <b>بازه زمانی:</b> <code>{config.START_DATE} → {config.END_DATE}</code>

🔢 <b>تعداد معاملات:</b> <code>{summary['total_trades']}</code>
✅ <b>تعداد سود:</b> <code>{summary['wins']}</code>
❌ <b>تعداد ضرر:</b> <code>{summary['losses']}</code>
📈 <b>نرخ موفقیت:</b> <code>{summary['win_rate']:.2f}%</code>
📉 <b>ماکزیمم Drawdown:</b> <code>{summary['max_drawdown']:.2f}%</code>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """

    await bot.send_message(
        chat_id=config.TELEGRAM_CHAT_ID,
        text=message,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )

    # ارسال جزئیات معاملات
    for idx, row in trades_df.iterrows():
        detail = f"""
🔁 <b>معامله #{idx+1} | {row['type'].upper()}</b>
──────────────────────────
📅 <b>تاریخ:</b> {row['entry_time']}
🟢 <b>قیمت ورود:</b> <code>{row['entry_price']:.6f}</code>
🎯 <b>TP1:</b> <code>{row['tp1']:.6f}</code>
🎯 <b>TP2:</b> <code>{row['tp2']:.6f}</code>
🎯 <b>TP3:</b> <code>{row['tp3']:.6f}</code>
💰 <b>سود/ضرر:</b> <code>{row['pnl']:+.2f}%</code>
        """

        await bot.send_message(
            chat_id=config.TELEGRAM_CHAT_ID,
            text=detail,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )

    # ارسال فایل معاملات
    with open("results/trades.csv", "rb") as f:
        await bot.send_document(
            chat_id=config.TELEGRAM_CHAT_ID,
            document=f,
            filename="معاملات.csv",
            caption="📎 فایل جزئیات معاملات"
        )

    print("✅ گزارش به تلگرام ارسال شد.")
