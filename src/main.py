# src/main.py
import time
import os
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

class TradingSystem:
    def __init__(self):
        self.connector = ExchangeConnector()
        self.strategy = InstitutionalStrategy()
        self.logger = TradeLogger()
        self.last_run = None

    def is_trading_active(self):
        now_utc = datetime.utcnow()
        current_time = now_utc.time()
        return dt_time(3, 0) <= current_time <= dt_time(20, 30)

    def calculate_sleep_time(self):
        now_utc = datetime.utcnow()
        if now_utc.time() > dt_time(20, 30):
            next_run = (now_utc + timedelta(days=1)).replace(hour=3, minute=0, second=0, microsecond=0)
        else:
            next_run = now_utc.replace(hour=3, minute=0, second=0, microsecond=0)
        return (next_run - now_utc).total_seconds()

    def run_single_check(self):
        try:
            print(f"\n{'='*50}")
            print(f"Checking at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

            df = self.connector.fetch_data(limit=100)
            print(f"Data from {self.connector.connected_exchange}")

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
                print(f"✅ Signal detected: Entry {signal_data['entry']:.2f}")
                send_signal(signal_data)
                return True
            else:
                print("❌ No signal detected")
                return False
        except Exception as e:
            print(f"❌ Error in check: {str(e)}")
            return False

    def run_continuous(self):
        print("🚀 Starting continuous trading mode...")
        schedule.every().day.at("20:25").do(self.generate_daily_report)

        while True:
            if not self.is_trading_active():
                sleep_time = self.calculate_sleep_time()
                print(f"💤 System sleeping until {datetime.utcnow() + timedelta(seconds=sleep_time)} UTC")
                time.sleep(sleep_time)
                continue

            self.run_single_check()
            time.sleep(900)  # 15 دقیقه

    def run_manual(self):
        print("🔧 Starting manual check...")
        if self.is_trading_active():
            print("✅ Market is active (03:00-20:30 UTC)")
        else:
            print("⏸️ Market is closed (20:30-03:00 UTC)")

        self.run_single_check()

    def generate_daily_report(self):
        reporter = DailyReporter(self.logger, self.strategy.get_filter_stats())
        reporter.generate_report()
        self.strategy.reset_stats()
        self.logger.clear_log()

    def run_backtest(self, start_date, end_date):
        print(f"\n📊 Running backtest from {start_date.date()} to {end_date.date()}")

        from backtester import Backtester
        backtester = Backtester(initial_balance=10000, commission=0.001)

        # شبیه‌سازی داده (در عمل از API بگیرید)
        print("⚠️ Note: Backtesting with simulated strategy logic.")
        df = self.connector.fetch_data(limit=1000)
        df = self.strategy.calculate(df)

        results = backtester.run_backtest(
            data=df,
            strategy_func=self.strategy.calculate,
            risk_per_trade=0.01,
            max_holding_period=24
        )

        backtester.generate_report("results/backtest")

        print("\n📈 Backtest Results:")
        print(f"Initial Balance: ${results['final_balance']:.2f}")
        print(f"Final Balance: ${results['final_balance']:.2f}")
        print(f"Total Return: {results['return_pct']:.2f}%")
        print(f"Win Rate: {results['win_rate']:.2f}%")
        print(f"Profit Factor: {results['profit_factor']:.2f}")

def main():
    parser = argparse.ArgumentParser(description='Bitcoin Institutional Trading System')
    parser.add_argument('--mode', choices=['live', 'manual', 'backtest'], default='manual')
    parser.add_argument('--start', help='Backtest start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='Backtest end date (YYYY-MM-DD)')

    args = parser.parse_args()
    system = TradingSystem()

    if args.mode == 'backtest':
        if not args.start or not args.end:
            print("❌ Error: --start and --end are required for backtest mode.")
            exit(1)
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
        end_date = datetime.strptime(args.end, "%Y-%m-%d")
        system.run_backtest(start_date, end_date)
    elif args.mode == 'live':
        system.run_continuous()
    else:
        system.run_manual()

if __name__ == "__main__":
    main()
