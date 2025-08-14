import time
import os
import pandas as pd
import numpy as np
from datetime import datetime, time, timedelta
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
        """بررسی زمان فعال بودن سیستم (03:00 تا 20:30 UTC)"""
        now_utc = datetime.utcnow()
        current_time = now_utc.time()
        return time(3, 0) <= current_time <= time(20, 30)

    def calculate_sleep_time(self):
        """محاسبه زمان باقیمانده تا فعال شدن مجدد"""
        now_utc = datetime.utcnow()
        if now_utc.time() > time(20, 30):
            return ((now_utc + timedelta(days=1)).replace(hour=3, minute=0, second=0) - now_utc).total_seconds()
        else:
            return (now_utc.replace(hour=3, minute=0, second=0) - now_utc).total_seconds()

    def run_single_check(self):
        """اجرای یک چرخه کامل بررسی سیگنال"""
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
                    'entry': latest['close'],
                    'sl': latest['stop_loss'],
                    'tp': latest['take_profit'],
                    'timestamp': latest['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.logger.log_signal(signal_data)
                print(f"Signal detected: Entry {signal_data['entry']:.2f}")
                send_signal(signal_data)
                return True
            else:
                print("No signal detected")
                return False
                
        except Exception as e:
            print(f"Error in check: {str(e)}")
            return False

    def run_continuous(self):
        """حالت اجرای خودکار پیوسته"""
        print("Starting continuous trading mode...")
        schedule.every().day.at("20:25").do(self.generate_daily_report)
        
        while True:
            if not self.is_trading_active():
                sleep_time = self.calculate_sleep_time()
                print(f"System sleeping until {datetime.utcnow() + timedelta(seconds=sleep_time)} UTC")
                time.sleep(sleep_time)
                continue
                
            self.run_single_check()
            time.sleep(900)  # 15 دقیقه انتظار

    def run_manual(self):
        """حالت اجرای دستی"""
        print("Starting manual check...")
        if self.is_trading_active():
            print("Market is active (03:00-20:30 UTC)")
            result = self.run_single_check()
            print(f"Manual check {'successful' if result else 'completed with no signal'}")
        else:
            print("Market is closed (20:30-03:00 UTC)")
            print("You can still run checks manually during inactive hours")
            if input("Continue anyway? (y/n): ").lower() == 'y':
                self.run_single_check()

    def generate_daily_report(self):
        """تولید گزارش روزانه"""
        reporter = DailyReporter(self.logger, self.strategy.get_filter_stats())
        reporter.generate_report()
        self.strategy.reset_stats()
        self.logger.clear_log()

    def run_backtest(self, start_date, end_date):
        """اجرای بک‌تست تاریخی"""
        print(f"\nRunning backtest from {start_date} to {end_date}")
        
        all_data = []
        current_date = start_date
        while current_date <= end_date:
            print(f"Fetching data for {current_date.strftime('%Y-%m')}")
            df = self.connector.fetch_data(limit=500)
            all_data.append(df)
            current_date += timedelta(days=30)
        
        full_df = pd.concat(all_data).drop_duplicates().sort_values('timestamp')
        print(f"Total data points: {len(full_df)}")
        
        full_df = self.strategy.calculate(full_df)
        
        from backtester import Backtester
        backtester = Backtester(self.strategy.get_filter_stats())
        results = backtester.backtest(full_df)
        
        os.makedirs("results", exist_ok=True)
        results_file = f"results/backtest_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        pd.DataFrame(results['trades']).to_csv(results_file, index=False)
        
        print("\nBacktest Results:")
        print(f"Initial Balance: ${results['initial_balance']:.2f}")
        print(f"Final Balance: ${results['final_balance']:.2f}")
        print(f"Profit: {results['profit_pct']:.2f}%")
        print(f"Total Trades: {len(results['trades'])}")

def main():
    parser = argparse.ArgumentParser(
        description='Bitcoin Institutional Trading System',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Examples:
  Live mode:    python main.py --mode live
  Manual check: python main.py --mode manual
  Backtest:     python main.py --mode backtest --start 2023-01-01 --end 2023-12-31""")
    
    parser.add_argument('--mode', choices=['live', 'manual', 'backtest'], default='manual',
                      help='Operation mode (default: manual)')
    parser.add_argument('--start', help='Backtest start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='Backtest end date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    system = TradingSystem()
    
    if args.mode == 'backtest':
        if not args.start or not args.end:
            print("Error: Please specify both start and end dates")
            print("Example: python main.py --mode backtest --start 2023-01-01 --end 2023-12-31")
            exit(1)
        
        try:
            start_date = datetime.strptime(args.start, "%Y-%m-%d")
            end_date = datetime.strptime(args.end, "%Y-%m-%d")
            system.run_backtest(start_date, end_date)
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD")
    elif args.mode == 'live':
        system.run_continuous()
    else:
        system.run_manual()

if __name__ == "__main__":
    main()
