# src/main.py
import time
import os
import logging
import pandas as pd
from datetime import datetime, time as dt_time, timedelta
from exchange_connector import ExchangeConnector
from strategy_engine import InstitutionalStrategy
from trade_logger import TradeLogger
from telegram_bot import send_signal
from daily_reporter import DailyReporter
import config
import schedule
import argparse

# تنظیم سیستم لاگینگ
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("logs/trading.log", encoding='utf-8'),
        logging.StreamHandler()  # نمایش در کنسول
    ]
)
logger = logging.getLogger(__name__)

class TradingSystem:
    def __init__(self):
        self.connector = ExchangeConnector()
        self.strategy = InstitutionalStrategy()
        self.logger = TradeLogger()
        self.last_run = None
        logger.info("✅ سیستم معاملاتی راه‌اندازی شد")

    def is_trading_active(self):
        now_utc = datetime.utcnow()
        current_time = now_utc.time()
        active = dt_time(3, 0) <= current_time <= dt_time(20, 30)
        if active:
            logger.info("🟢 بازار فعال است (03:00-20:30 UTC)")
        else:
            logger.warning("🔴 بازار بسته است، سیستم در حالت استراحت")
        return active

    def calculate_sleep_time(self):
        now_utc = datetime.utcnow()
        if now_utc.time() > dt_time(20, 30):
            next_run = (now_utc + timedelta(days=1)).replace(hour=3, minute=0, second=0, microsecond=0)
        else:
            next_run = now_utc.replace(hour=3, minute=0, second=0, microsecond=0)
        sleep_time = (next_run - now_utc).total_seconds()
        logger.info(f"💤 سیستم برای {sleep_time:.0f} ثانیه می‌خوابد تا {next_run.strftime('%H:%M:%S')} UTC")
        return sleep_time

    def run_single_check(self):
        try:
            logger.info("="*50)
            logger.info(f"🔄 بررسی جدید در {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

            df = self.connector.fetch_data(limit=100)
            logger.info(f"📥 داده از صرافی {self.connector.connected_exchange} دریافت شد | {len(df)} کندل")

            df = self.strategy.calculate(df)
            latest = df.iloc[-1]

            if latest['signal'] == 1:
                signal_data = {
                    'symbol': config.SYMBOL,
                    'signal': 1,
                    'entry': float(latest['close']),
                    'sl': float(latest['stop_loss']),
                    'tp': float(latest['take_profit']),
                    'timestamp': latest['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                }
                self.logger.log_signal(signal_data)
                logger.info(f"🟢 سیگنال خرید تشخیص داده شد | ورود: {signal_data['entry']:.2f} | SL: {signal_data['sl']:.2f} | TP: {signal_data['tp']:.2f}")
                send_signal(signal_data)
                return True
            else:
                logger.info("🟡 هیچ سیگنالی تشخیص داده نشد")
                return False

        except Exception as e:
            logger.error(f"❌ خطای جدی در run_single_check: {str(e)}", exc_info=True)
            return False

    def run_continuous(self):
        logger.info("🚀 حالت اجرای پیوسته فعال شد...")
        schedule.every().day.at("20:25").do(self.generate_daily_report)

        while True:
            if not self.is_trading_active():
                sleep_time = self.calculate_sleep_time()
                time.sleep(sleep_time)
                continue

            self.run_single_check()
            logger.debug("⏳ 15 دقیقه تاخیر قبل از بررسی بعدی...")
            time.sleep(900)

    def run_manual(self):
        logger.info("🔧 حالت دستی فعال شد")
        self.run_single_check()

    def generate_daily_report(self):
        logger.info("📊 تولید گزارش روزانه...")
        reporter = DailyReporter(self.logger, self.strategy.get_filter_stats())
        reporter.generate_report()
        self.strategy.reset_stats()
        self.logger.clear_log()
        logger.info("✅ گزارش روزانه تولید و آمار ریست شد")

    def run_backtest(self, start_date, end_date):
        logger.info(f"📊 بک‌تست از {start_date.date()} تا {end_date.date()}")
        from backtester import Backtester
        backtester = Backtester(initial_balance=10000, commission=0.001)

        df = self.connector.fetch_data(limit=1000)
        df = self.strategy.calculate(df)

        results = backtester.run_backtest(
            data=df,
            strategy_func=self.strategy.calculate,
            risk_per_trade=0.01,
            max_holding_period=24
        )

        backtester.generate_report("results/backtest")

        logger.info("\n📈 نتایج بک‌تست:")
        logger.info(f"موجودی اولیه: ${results['final_balance']:.2f}")
        logger.info(f"موجودی نهایی: ${results['final_balance']:.2f}")
        logger.info(f"بازده کلی: {results['return_pct']:.2f}%")
        logger.info(f"نرخ برد: {results['win_rate']:.2f}%")
        logger.info(f"فاکتور سود: {results['profit_factor']:.2f}")

def main():
    parser = argparse.ArgumentParser(description='Bitcoin Institutional Trading System')
    parser.add_argument('--mode', choices=['live', 'manual', 'backtest'], default='manual')
    parser.add_argument('--start', help='Backtest start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='Backtest end date (YYYY-MM-DD)')

    args = parser.parse_args()
    system = TradingSystem()

    if args.mode == 'backtest':
        if not args.start or not args.end:
            logger.error("❌ خطای ورودی: --start و --end برای حالت بک‌تست الزامی هستند")
            exit(1)
        try:
            start_date = datetime.strptime(args.start, "%Y-%m-%d")
            end_date = datetime.strptime(args.end, "%Y-%m-%d")
            system.run_backtest(start_date, end_date)
        except ValueError as e:
            logger.error(f"❌ فرمت تاریخ نامعتبر: {str(e)}")
    elif args.mode == 'live':
        system.run_continuous()
    else:
        system.run_manual()

if __name__ == "__main__":
    main()
