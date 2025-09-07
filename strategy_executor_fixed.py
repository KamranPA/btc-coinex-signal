#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ربات اجرای استراتژی معاملاتی - نسخه اصلاح شده
رفع خطای: list indices must be integers or slices, not str
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Union
import requests
import pandas as pd
import numpy as np

# تنظیمات پیشرفته لاگ‌گیری
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('strategy_executor')

class BinanceAPI:
    """کلاس برای ارتباط با API صرافی Binance"""
    
    def __init__(self, api_key: str = "", api_secret: str = ""):
        self.base_url = "https://api.binance.com/api/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': api_key,
            'Content-Type': 'application/json'
        })
        self.api_secret = api_secret

    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> Optional[List[Dict]]:
        """دریافت داده‌های کندل استیک"""
        try:
            url = f"{self.base_url}/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"داده‌های {symbol} دریافت شد. تعداد کندل‌ها: {len(data)}")
            
            # تبدیل به ساختار استاندارد
            candles = []
            for candle in data:
                candles.append({
                    'timestamp': candle[0],
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            return candles
            
        except Exception as e:
            logger.error(f"خطا در دریافت داده‌های {symbol}: {e}")
            return None

class DataValidator:
    """کلاس برای اعتبارسنجی و بررسی ساختار داده‌ها"""
    
    @staticmethod
    def validate_data(data: Any, symbol: str) -> Optional[List[Dict]]:
        """اعتبارسنجی ساختار داده‌های دریافتی"""
        
        if data is None:
            logger.warning(f"داده‌های {symbol} None است")
            return None
        
        # اگر داده لیست است
        if isinstance(data, list):
            if len(data) == 0:
                logger.warning(f"لیست داده‌های {symbol} خالی است")
                return None
            
            # بررسی اینکه آیتم‌های لیست دیکشنری هستند
            first_item = data[0]
            if isinstance(first_item, dict):
                logger.info(f"داده‌های {symbol} معتبر است (لیست دیکشنری)")
                return data
            else:
                logger.warning(f"آیتم‌های لیست {symbol} از نوع دیکشنری نیستند: {type(first_item)}")
                return None
        
        # اگر داده دیکشنری است
        elif isinstance(data, dict):
            logger.info(f"داده‌های {symbol} دیکشنری است. کلیدها: {list(data.keys())}")
            
            # جستجوی کلیدهای معمول حاوی داده‌های لیستی
            list_keys = ['data', 'result', 'candles', 'klines', 'series', 'items']
            
            for key in list_keys:
                if key in data and isinstance(data[key], list):
                    if len(data[key]) > 0:
                        logger.info(f"داده‌های لیستی در کلید '{key}' یافت شد")
                        return data[key]
            
            # اگر هیچ کلید لیستی پیدا نشد
            logger.error(f"هیچ داده لیستی در دیکشنری {symbol} یافت نشد")
            return None
        
        else:
            logger.error(f"نوع داده نامعتبر برای {symbol}: {type(data)}")
            return None

class TradingStrategy:
    """کلاس پایه برای استراتژی‌های معاملاتی"""
    
    def __init__(self):
        self.name = "RSI_Strategy"
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """محاسبه RSI"""
        if len(prices) < period + 1:
            return [50] * len(prices)  # مقدار پیش‌فرض
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        rsi_values = []
        for i in range(len(prices) - 1):
            if i >= period:
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        # اضافه کردن مقدار برای آخرین قیمت
        rsi_values.append(rsi_values[-1] if rsi_values else 50)
        
        return rsi_values
    
    def generate_signal(self, symbol: str, market_data: List[Dict]) -> Optional[Dict[str, Any]]:
        """تولید سیگنال معاملاتی"""
        try:
            if not market_data or len(market_data) < 20:
                logger.warning(f"داده‌های ناکافی برای {symbol}")
                return None
            
            # استخراج قیمت‌های بسته‌ شدن
            closes = [candle['close'] for candle in market_data]
            
            # محاسبه RSI
            rsi_values = self.calculate_rsi(closes)
            current_rsi = rsi_values[-1]
            
            # منطق ساده سیگنال‌دهی
            signal = "HOLD"
            if current_rsi < 30:
                signal = "BUY"
            elif current_rsi > 70:
                signal = "SELL"
            
            # ایجاد سیگنال
            latest_candle = market_data[-1]
            signal_data = {
                'symbol': symbol,
                'signal': signal,
                'price': latest_candle['close'],
                'rsi': round(current_rsi, 2),
                'timestamp': latest_candle['timestamp'],
                'confidence': abs(current_rsi - 50) / 50  # اطمینان بر اساس فاصله از 50
            }
            
            logger.info(f"سیگنال {symbol}: {signal} (RSI: {current_rsi:.2f})")
            return signal_data
            
        except Exception as e:
            logger.error(f"خطا در تولید سیگنال برای {symbol}: {e}")
            return None

class StrategyExecutor:
    """اجراکننده اصلی استراتژی"""
    
    def __init__(self):
        self.api = BinanceAPI()
        self.validator = DataValidator()
        self.strategy = TradingStrategy()
        self.symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "XRPUSDT"]
    
    def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """تحلیل یک نماد"""
        logger.info(f"🔍 در حال تحلیل {symbol}...")
        
        try:
            # دریافت داده‌های بازار
            raw_data = self.api.get_klines(symbol)
            
            # اعتبارسنجی داده‌ها
            validated_data = self.validator.validate_data(raw_data, symbol)
            if validated_data is None:
                logger.warning(f"داده‌های {symbol} نامعتبر است")
                return None
            
            # تولید سیگنال
            signal = self.strategy.generate_signal(symbol, validated_data)
            return signal
            
        except Exception as e:
            logger.error(f"خطا در تحلیل {symbol}: {e}")
            return None
    
    def run_analysis(self):
        """اجرای تحلیل برای تمام نمادها"""
        logger.info("🚀 شروع تحلیل نمادها...")
        results = {}
        
        for symbol in self.symbols:
            signal = self.analyze_symbol(symbol)
            if signal:
                results[symbol] = signal
            else:
                logger.warning(f"تحلیل {symbol} ناموفق بود")
            
            # تاخیر کوتاه برای جلوگیری از Rate Limit
            time.sleep(1)
        
        return results
    
    def print_results(self, results: Dict):
        """نمایش نتایج تحلیل"""
        print("\n" + "="*60)
        print("📊 نتایج تحلیل سیگنال‌ها:")
        print("="*60)
        
        for symbol, signal_data in results.items():
            print(f"{symbol}:")
            print(f"  📈 سیگنال: {signal_data['signal']}")
            print(f"  💰 قیمت: {signal_data['price']:.4f}")
            print(f"  📊 RSI: {signal_data['rsi']}")
            print(f"  🎯 اطمینان: {signal_data['confidence']:.2%}")
            print(f"  ⏰ زمان: {pd.to_datetime(signal_data['timestamp'], unit='ms')}")
            print("-" * 40)

def main():
    """تابع اصلی"""
    try:
        print("🤖 ربات تحلیل سیگنال راه‌اندازی شد...")
        print("📡 در حال اتصال به API Binance...")
        
        executor = StrategyExecutor()
        results = executor.run_analysis()
        
        if results:
            executor.print_results(results)
            print(f"\n✅ تحلیل با موفقیت انجام شد. تعداد سیگنال‌ها: {len(results)}")
        else:
            print("\n❌ هیچ سیگنالی تولید نشد!")
            
    except KeyboardInterrupt:
        print("\n⏹️  ربات متوقف شد")
    except Exception as e:
        print(f"\n💥 خطای غیرمنتظره: {e}")
        logger.exception("خطای جزئی:")

if __name__ == "__main__":
    main()
