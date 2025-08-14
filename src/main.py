import os
import time
import pandas as pd
from datetime import datetime, time, timedelta
from exchange_connector import ExchangeConnector
from strategy_engine import InstitutionalStrategy
from trade_logger import TradeLogger
from telegram_bot import send_signal
from daily_reporter import DailyReporter
import config
import schedule
import argparse
import sys

class TradingSystem:
    def __init__(self):
        self.connector = ExchangeConnector()
        self.strategy = InstitutionalStrategy()
        self.logger = TradeLogger()
        self.last_run = None

    def is_trading_hours(self):
        """بررسی ساعات فعال بازار (03:00 تا 20:30 UTC)"""
        now = datetime.utcnow()
        current_time = now.time()
        return time(3, 0) <= current_time <= time(20, 30)

    def calculate_sleep_time(self):
        """محاسبه زمان باقیمانده تا بازگشایی بازار"""
        now = datetime.utcnow()
        if now.time() > time(20, 30):
            # فردا ساعت 03:00
            wakeup = (now + timedelta(days=1)).replace(hour=3, minute=0, second=0)
        else:
            # امروز ساعت 03:00
            wakeup = now.replace(hour=3, minute=0, second=0)
        return (wakeup - now).total_seconds()

    def run_single_check(self, force=False):
        """اجرای یک چرخه کامل بررسی بازار"""
        try:
            if not force and not self.is_trading_hours():
                print("⚠️ بازار خارج از ساعات فعال است (03:00-20:30 UTC)")
                return False

            print(f"\n{'='*50}")
            print(f"🔍 بررسی بازار در {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            # دریافت داده‌های بازار
            df = self.connector.fetch_data(limit=100)
            print(f"📊 داده‌ها دریافت شد از {self.connector.connected_exchange}")
            
            # تحلیل و شناسایی سیگنال
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
                print(f"🚨 سیگنال شناسایی شد! قیمت ورود: {signal_data['entry']:.2f}")
                send_signal(signal_data)
                return True
            else:
                print("🔍 هیچ سیگنالی شناسایی نشد")
                return False
                
        except Exception as e:
            print(f"❌ خطا در بررسی بازار: {str(e)}")
            return False

    def run_continuous(self):
        """حالت اجرای خودکار پیوسته"""
        print("🚀 شروع سیستم معاملاتی خودکار...")
        schedule.every().day.at("20:25").do(self.generate_daily_report)
        
        while True:
            if not self.is_trading_hours():
                sleep_time = self.calculate_sleep_time()
                wake_time = datetime.utcnow() + timedelta(seconds=sleep_time)
                print(f"💤 سیستم تا {wake_time.strftime('%Y-%m-%d %H:%M:%S')} UTC به خواب می‌رود")
                time.sleep(sleep_time)
                continue
                
            self.run_single_check()
            time.sleep(900)  # هر 15 دقیقه

    def run_manual(self, force=False):
        """حالت اجرای دستی"""
        print("\n🔧 حالت اجرای دستی فعال شد")
        if force or self.is_trading_hours():
            result = self.run_single_check(force=True)
            status = "✅ موفق" if result else "🔍 بدون سیگنال"
            print(f"\n🏁 نتیجه بررسی: {status}")
        else:
            print("⚠️ هشدار: بازار خارج از ساعات فعال است (03:00-20:30 UTC)")
            if input("🔹 آیا می‌خواهید ادامه دهید؟ (y/n): ").lower() == 'y':
                self.run_single_check(force=True)

    def generate_daily_report(self):
        """تولید گزارش روزانه"""
        print("\n📊 در حال تولید گزارش روزانه...")
        reporter = DailyReporter(self.logger, self.strategy.get_filter_stats())
        reporter.generate_report()
        self.strategy.reset_stats()
        self.logger.clear_log()
        print("📩 گزارش روزانه ارسال شد")

    def run_backtest(self, start_date, end_date):
        """اجرای بک‌تست تاریخی"""
        print(f"\n📈 شروع بک‌تست از {start_date} تا {end_date}")
        
        try:
            # جمع‌آوری داده‌های تاریخی
            all_data = []
            current_date = start_date
            
            while current_date <= end_date:
                print(f"📥 دریافت داده برای {current_date.strftime('%Y-%m')}...")
                df = self.connector.fetch_data(limit=500)
                all_data.append(df)
                current_date += timedelta(days=30)
            
            full_df = pd.concat(all_data).drop_duplicates().sort_values('timestamp')
            print(f"📊 تعداد داده‌های تاریخی: {len(full_df)}")
            
            # تحلیل داده‌ها
            full_df = self.strategy.calculate(full_df)
            
            # اجرای بک‌تست
            from backtester import Backtester
            backtester = Backtester(self.strategy.get_filter_stats())
            results = backtester.backtest(full_df)
            
            # ذخیره نتایج
            os.makedirs("results", exist_ok=True)
            filename = f"backtest_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            pd.DataFrame(results['trades']).to_csv(f"results/{filename}", index=False)
            
            # نمایش نتایج
            print("\n📊 نتایج بک‌تست:")
            print(f"💰 سرمایه اولیه: ${results['initial_balance']:.2f}")
            print(f"💰 سرمایه نهایی: ${results['final_balance']:.2f}")
            print(f"📈 سود: {results['profit_pct']:.2f}%")
            print(f"🔢 تعداد معاملات: {len(results['trades'])}")
            
        except Exception as e:
            print(f"❌ خطا در اجرای بک‌تست: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description='سیستم معاملاتی نهادی بیت‌کوین',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
مثال‌های استفاده:
  حالت خودکار:    python main.py --mode live
  بررسی دستی:     python main.py --mode manual
  بررسی اجباری:   python main.py --mode manual --force
  اجرای بک‌تست:   python main.py --mode backtest --start 2023-01-01 --end 2023-12-31
""")
    
    parser.add_argument('--mode', choices=['live', 'manual', 'backtest'], default='manual',
                      help='حالت اجرا (پیش‌فرض: manual)')
    parser.add_argument('--start', help='تاریخ شروع بک‌تست (YYYY-MM-DD)')
    parser.add_argument('--end', help='تاریخ پایان بک‌تست (YYYY-MM-DD)')
    parser.add_argument('--force', action='store_true',
                      help='اجرای بررسی خارج از ساعات بازار (فقط در حالت manual)')
    
    args = parser.parse_args()
    
    system = TradingSystem()
    
    try:
        if args.mode == 'backtest':
            if not args.start or not args.end:
                print("❌ خطا: لطفا تاریخ شروع و پایان را مشخص کنید")
                print("مثال: python main.py --mode backtest --start 2023-01-01 --end 2023-12-31")
                sys.exit(1)
            
            start_date = datetime.strptime(args.start, "%Y-%m-%d")
            end_date = datetime.strptime(args.end, "%Y-%m-%d")
            system.run_backtest(start_date, end_date)
            
        elif args.mode == 'live':
            system.run_continuous()
            
        else:
            system.run_manual(force=args.force)
            
    except KeyboardInterrupt:
        print("\n🛑 سیستم به صورت دستی متوقف شد")
    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
