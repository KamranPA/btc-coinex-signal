#!/usr/bin/env python3
"""
CoinEx Signal Bot - Main Entry Point
سیستم ارسال سیگنال‌های معاملاتی اتوماتیک برای CoinEx
"""

import sys
import os
import time
import pandas as pd
import numpy as np
from datetime import datetime

# اضافه کردن مسیر پروژه به sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from services.coinex_api import CoinExAPI
    from services.telegram_bot import TelegramBot
    from strategies.mutanabby_strategy import MutanabbyStrategy
    from config.config import SYMBOLS, TIMEFRAME, SENSITIVITY, SIGNAL_TUNER
    print("✅ تمام ماژول‌ها با موفقیت import شدند")
except ImportError as e:
    print(f"❌ خطا در import ماژول‌ها: {e}")
    print("📁 در حال بررسی ساختار پروژه...")
    
    # ایجاد ساختار پایه اگر ماژول‌ها وجود ندارند
    if not os.path.exists('services'):
        os.makedirs('services')
        with open('services/__init__.py', 'w') as f:
            f.write('# Services package\n')
    
    if not os.path.exists('strategies'):
        os.makedirs('strategies')
        with open('strategies/__init__.py', 'w') as f:
            f.write('# Strategies package\n')
    
    if not os.path.exists('config'):
        os.makedirs('config')
        with open('config/__init__.py', 'w') as f:
            f.write('# Config package\n')
    
    print("📦 ساختار پایه ایجاد شد. لطفا فایل‌های لازم را اضافه کنید.")
    sys.exit(1)

class CoinExSignalBot:
    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.coinex_api = CoinExAPI()
        self.telegram_bot = TelegramBot()
        self.strategy = MutanabbyStrategy()
        
        print("🤖 CoinEx Signal Bot initialized")
        print(f"🎯 نمادها: {SYMBOLS}")
        print(f"⏰ تایم فریم: {TIMEFRAME}")
        print(f"🎚️ حساسیت: {SENSITIVITY}")
        print(f"⚙️ تنظیم کننده سیگنال: {SIGNAL_TUNER}")
    
    def fetch_market_data(self, symbol, timeframe, limit=100):
        """دریافت داده‌های بازار از CoinEx"""
        try:
            print(f"📡 دریافت داده برای {symbol}...")
            market_data = self.coinex_api.get_market_data(symbol, 'kline', limit, timeframe)
            
            if not market_data:
                print(f"⚠️ هیچ داده‌ای برای {symbol} دریافت نشد")
                return None
            
            # تبدیل داده‌ها به DataFrame
            df = pd.DataFrame(market_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('timestamp', inplace=True)
            
            # تبدیل مقادیر به عدد
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            print(f"✅ داده‌های {symbol} پردازش شدند ({len(df)} کندل)")
            return df
            
        except Exception as e:
            print(f"❌ خطا در دریافت داده‌های {symbol}: {e}")
            return None
    
    def generate_signals(self, df, symbol):
        """تولید سیگنال‌های معاملاتی"""
        try:
            if df is None or len(df) < 50:
                print(f"⚠️ داده‌های ناکافی برای {symbol}")
                return []
            
            signals = self.strategy.generate_signals(df)
            print(f"📈 {len(signals)} سیگنال برای {symbol} تولید شد")
            return signals
            
        except Exception as e:
            print(f"❌ خطا در تولید سیگنال‌های {symbol}: {e}")
            return []
    
    def send_signals(self, signals, symbol):
        """ارسال سیگنال‌ها به تلگرام"""
        if not signals:
            return 0
        
        sent_count = 0
        for signal in signals:
            try:
                message = self.telegram_bot.format_signal_message(
                    symbol=symbol,
                    signal_type='خرید' if signal['type'] == 'BUY' else 'فروش',
                    entry=round(signal['entry'], 4),
                    sl=round(signal['sl'], 4),
                    tp1=round(signal['tp1'], 4),
                    tp2=round(signal['tp2'], 4),
                    tp3=round(signal['tp3'], 4)
                )
                
                if self.test_mode:
                    print(f"🧪 حالت تست - سیگنال برای {symbol}:")
                    print(message)
                    sent_count += 1
                else:
                    if self.telegram_bot.send_message(message):
                        print(f"✅ سیگنال برای {symbol} ارسال شد")
                        sent_count += 1
                    else:
                        print(f"❌ ارسال سیگنال برای {symbol} ناموفق بود")
                
                # تاخیر بین ارسال سیگنال‌ها
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ خطا در ارسال سیگنال برای {symbol}: {e}")
        
        return sent_count
    
    def run(self):
        """اجرای اصلی ربات"""
        print("\n" + "="*60)
        print("🚀 شروع اجرای CoinEx Signal Bot")
        print("="*60)
        
        total_signals = 0
        start_time = time.time()
        
        for symbol in SYMBOLS:
            try:
                print(f"\n🎯 پردازش نماد: {symbol}")
                
                # دریافت داده‌های بازار
                df = self.fetch_market_data(symbol, TIMEFRAME)
                if df is None:
                    continue
                
                # تولید سیگنال‌ها
                signals = self.generate_signals(df, symbol)
                
                # ارسال سیگنال‌ها
                if signals:
                    sent_count = self.send_signals(signals, symbol)
                    total_signals += sent_count
                else:
                    print(f"📊 هیچ سیگنالی برای {symbol} یافت نشد")
                
            except Exception as e:
                print(f"💥 خطای غیرمنتظره در پردازش {symbol}: {e}")
                continue
        
        # گزارش نهایی
        execution_time = time.time() - start_time
        print("\n" + "="*60)
        print("📊 گزارش نهایی اجرا")
        print("="*60)
        print(f"✅ تعداد نمادهای پردازش شده: {len(SYMBOLS)}")
        print(f"✅ تعداد سیگنال‌های ارسال شده: {total_signals}")
        print(f"⏱️ زمان اجرا: {execution_time:.2f} ثانیه")
        print(f"🧪 حالت تست: {'فعال' if self.test_mode else 'غیرفعال'}")
        print("="*60)
        
        return total_signals

def main():
    """تابع اصلی"""
    print("🤖 CoinEx Signal Bot")
    print("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # بررسی آرگومان‌های خط فرمان
    test_mode = '--test' in sys.argv or '-t' in sys.argv
    
    if test_mode:
        print("🧪 اجرا در حالت تست (سیگنال‌ها ارسال نمی‌شوند)")
    
    try:
        # ایجاد و اجرای ربات
        bot = CoinExSignalBot(test_mode=test_mode)
        signals_sent = bot.run()
        
        if signals_sent > 0:
            print(f"🎉 اجرا با موفقیت завер شد. {signals_sent} سیگنال ارسال شد.")
        else:
            print("ℹ️ اجرا کامل شد، اما هیچ سیگنالی ارسال نشد.")
            
    except KeyboardInterrupt:
        print("\n⏹️ اجرا توسط کاربر متوقف شد")
    except Exception as e:
        print(f"💥 خطای غیرمنتظره: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✨ پایان برنامه")

if __name__ == "__main__":
    main()
