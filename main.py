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

def is_trading_active():
    """
    بررسی آیا سیستم باید فعال باشد یا خیر
    فعال در ساعات 03:00 تا 20:30 UTC
    """
    now_utc = datetime.utcnow()
    current_time = now_utc.time()
    
    # تعریف بازه‌های زمانی فعال
    active_start = time(3, 0)      # 03:00 UTC
    active_end = time(20, 30)      # 20:30 UTC
    
    # اگر زمان فعلی بین 03:00 تا 20:30 باشد
    if active_start <= current_time <= active_end:
        return True
    
    return False

def calculate_sleep_time():
    """محاسبه زمان خواب تا فعال شدن مجدد سیستم"""
    now_utc = datetime.utcnow()
    
    # اگر بعد از 20:30 UTC هستیم
    if now_utc.time() > time(20, 30):
        # فعال شدن در 03:00 فردا
        next_day = now_utc + timedelta(days=1)
        wakeup_time = datetime(next_day.year, next_day.month, next_day.day, 3, 0)
    else:  # اگر قبل از 03:00 UTC هستیم
        # فعال شدن در 03:00 امروز
        wakeup_time = datetime(now_utc.year, now_utc.month, now_utc.day, 3, 0)
    
    return (wakeup_time - now_utc).total_seconds()

def generate_daily_report(strategy, logger):
    """تولید و ارسال گزارش روزانه"""
    reporter = DailyReporter(logger, strategy.get_filter_stats())
    report = reporter.generate_report()
    strategy.reset_stats()
    logger.clear_log()
    print("Daily report generated and sent")

def run_live():
    """اجرای اصلی سیستم در حالت معاملات زنده"""
    print("Starting live trading system...")
    print(f"Current UTC time: {datetime.utcnow()}")
    
    connector = ExchangeConnector()
    strategy = InstitutionalStrategy()
    logger = TradeLogger()
    
    # زمان‌بندی برای گزارش روزانه (هر روز ساعت 20:25 UTC)
    schedule.every().day.at("20:25").do(
        lambda: generate_daily_report(strategy, logger)
    )
    
    while True:
        try:
            # اجرای وظایف زمان‌بندی شده (گزارش روزانه)
            schedule.run_pending()
            
            # بررسی زمان فعال بودن سیستم
            if not is_trading_active():
                sleep_seconds = calculate_sleep_time()
                print(f"System sleeping. Will resume at {datetime.utcnow() + timedelta(seconds=sleep_seconds)} UTC")
                time.sleep(sleep_seconds)
                continue
            
            print(f"\n{'='*50}")
            print(f"Fetching new data at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            # دریافت داده‌های جدید (100 کندل آخر)
            df = connector.fetch_data(limit=100)
            print(f"Data fetched from {connector.connected_exchange}")
            
            # محاسبه سیگنال با استراتژی نهادی
            df = strategy.calculate(df)
            latest = df.iloc[-1]
            
            # بررسی وجود سیگنال جدید
            if latest['signal'] == 1:
                signal_data = {
                    'symbol': config.SYMBOL,
                    'signal': 1,
                    'entry': latest['close'],
                    'sl': latest['stop_loss'],
                    'tp': latest['take_profit'],
                    'timestamp': latest['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # ثبت سیگنال در سیستم
                logger.log_signal(signal_data)
                print(f"New signal detected at {signal_data['timestamp']}")
                print(f"Entry: {signal_data['entry']:.2f}, SL: {signal_data['sl']:.2f}, TP: {signal_data['tp']:.2f}")
                
                # ارسال سیگنال به تلگرام
                send_signal(signal_data)
                print("Signal sent to Telegram")
            else:
                print("No new signals detected")
            
            # نمایش آماری فیلترها
            print("\nFilter Statistics:")
            for filter_name, count in strategy.get_filter_stats().items():
                print(f"- {filter_name}: {count} times")
            
            print(f"{'='*50}\n")
            
        except Exception as e:
            print(f"Error: {str(e)}")
        
        # انتظار 15 دقیقه تا اجرای بعدی
        print(f"Waiting 15 minutes until next check...")
        time.sleep(900)

def run_backtest(start_date, end_date):
    """اجرای سیستم در حالت بک‌تست"""
    print("Starting backtest...")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    connector = ExchangeConnector()
    strategy = InstitutionalStrategy()
    logger = TradeLogger()
    
    # دریافت داده‌های تاریخی
    print("\nFetching historical data...")
    all_data = []
    current_date = start_date
    
    while current_date <= end_date:
        print(f"- Fetching data for {current_date.strftime('%Y-%m')}")
        df = connector.fetch_data(limit=500)
        all_data.append(df)
        current_date += timedelta(days=30)
    
    full_df = pd.concat(all_data).drop_duplicates().sort_values('timestamp')
    print(f"Total data points: {len(full_df)}")
    
    # محاسبه سیگنال‌ها
    print("\nCalculating signals...")
    full_df = strategy.calculate(full_df)
    
    # اجرای بک‌تست
    print("\nRunning backtest...")
    from backtester import Backtester
    backtester = Backtester(strategy.get_filter_stats())
    results = backtester.backtest(full_df)
    
    # ذخیره نتایج
    os.makedirs("results", exist_ok=True)
    results_file = f"results/backtest_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
    pd.DataFrame(results['trades']).to_csv(results_file, index=False)
    
    # تولید گزارش
    from analyzer import ResultAnalyzer
    analyzer = ResultAnalyzer(results)
    report = analyzer.generate_report()
    
    print("\nBacktest completed!")
    print(f"{'='*50}")
    print(f"Initial Balance: ${results['initial_balance']:.2f}")
    print(f"Final Balance: ${results['final_balance']:.2f}")
    print(f"Profit: {results['profit_pct']:.2f}%")
    print(f"Total Trades: {len(results['trades'])}")
    print(f"Win Rate: {report['performance']['win_rate']:.2f}%")
    
    # ذخیره گزارش خلاصه
    with open(f"results/summary_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.txt", "w") as f:
        f.write(f"Backtest Report ({start_date} to {end_date})\n")
        f.write("="*50 + "\n")
        f.write(f"Profit: {results['profit_pct']:.2f}%\n")
        f.write(f"Trades: {len(results['trades'])}\n")
        f.write(f"Win Rate: {report['performance']['win_rate']:.2f}%\n")
        f.write("\nFilter Statistics:\n")
        for filter_name, count in strategy.get_filter_stats().items():
            f.write(f"- {filter_name}: {count} times\n")
    
    print("Results saved in 'results' directory")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Bitcoin Institutional Trading System')
    parser.add_argument('--mode', choices=['live', 'backtest'], default='live', help='Operation mode')
    parser.add_argument('--start', help='Backtest start date (YYYY-MM-DD)')
    parser.add_argument('--end', help='Backtest end date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    if args.mode == 'backtest':
        if not args.start or not args.end:
            print("Error: Please specify start and end dates for backtest")
            print("Example: python main.py --mode backtest --start 2023-01-01 --end 2023-06-30")
            exit(1)
        
        try:
            start_date = datetime.strptime(args.start, "%Y-%m-%d")
            end_date = datetime.strptime(args.end, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD")
            exit(1)
            
        run_backtest(start_date, end_date)
    else:
        run_live()
