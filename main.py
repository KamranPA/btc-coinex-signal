#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
import json
from typing import Dict, Any, List, Optional, Union
import requests
import pandas as pd
import numpy as np

# تنظیمات لاگ‌گیری
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('signal_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('strategy_executor')

class CryptoDataFetcher:
    """کلاس دریافت داده از APIهای مختلف"""
    
    def __init__(self):
        self.binance_url = "https://api.binance.com/api/v3"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_binance_klines(self, symbol: str, interval: str = "1h", limit: int = 100) -> Optional[List[Dict]]:
        """دریافت داده از Binance"""
        try:
            url = f"{self.binance_url}/klines"
            params = {
                'symbol': symbol.upper(),
                'interval': interval,
                'limit': limit
            }
            
            logger.info(f"دریافت داده برای {symbol} از Binance...")
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # تبدیل داده به فرمت استاندارد
            formatted_data = []
            for item in data:
                if isinstance(item, list) and len(item) >= 6:
                    formatted_data.append({
                        'timestamp': item[0],
                        'open': float(item[1]),
                        'high': float(item[2]),
                        'low': float(item[3]),
                        'close': float(item[4]),
                        'volume': float(item[5]),
                        'symbol': symbol
                    })
            
            logger.info(f"تعداد داده‌های دریافت شده برای {symbol}: {len(formatted_data)}")
            return formatted_data
            
        except Exception as e:
            logger.error(f"خطا در دریافت داده از Binance برای {symbol}: {e}")
            return None
    
    def fetch_data(self, symbol: str, source: str = "binance", **kwargs) -> Optional[List[Dict]]:
        """دریافت داده از منبع مشخص"""
        if source.lower() == "binance":
            return self.fetch_binance_klines(symbol, **kwargs)
        else:
            logger.error(f"منبع داده پشتیبانی نمی‌شود: {source}")
            return None

class DataProcessor:
    """پردازش و اعتبارسنجی داده‌ها"""
    
    @staticmethod
    def safe_data_access(data: Any, symbol: str) -> Optional[List[Dict]]:
        """
        دسترسی ایمن به داده‌ها با رفع خطای list indices must be integers or slices, not str
        """
        try:
            if data is None:
                logger.warning(f"داده‌های {symbol} None است")
                return None
            
            # اگر داده مستقیماً لیست است
            if isinstance(data, list):
                if len(data) == 0:
                    logger.warning(f"لیست داده‌های {symbol} خالی است")
                    return None
                
                # بررسی نوع آیتم‌های لیست
                first_item = data[0]
                if isinstance(first_item, dict):
                    logger.info(f"داده‌های {symbol} معتبر است (لیست دیکشنری)")
                    return data
                elif isinstance(first_item, (list, tuple)):
                    logger.info(f"داده‌های {symbol} لیست لیست است - تبدیل به دیکشنری")
                    return DataProcessor.convert_list_to_dict(data, symbol)
                else:
                    logger.error(f"نوع آیتم‌های لیست نامعتبر برای {symbol}: {type(first_item)}")
                    return None
            
            # اگر داده دیکشنری است
            elif isinstance(data, dict):
                logger.info(f"داده‌های {symbol} دیکشنری است. کلیدها: {list(data.keys())}")
                
                # جستجوی کلیدهای معمول حاوی داده
                possible_keys = ['data', 'result', 'candles', 'klines', 'series', 'items', 'values']
                
                for key in possible_keys:
                    if key in data:
                        key_data = data[key]
                        if isinstance(key_data, list):
                            if len(key_data) > 0:
                                logger.info(f"داده لیستی در کلید '{key}' یافت شد")
                                return key_data
                        else:
                            logger.warning(f"کلید '{key}' وجود دارد اما لیست نیست: {type(key_data)}")
                
                logger.error(f"هیچ داده لیستی در دیکشنری {symbol} یافت نشد")
                return None
            
            else:
                logger.error(f"نوع داده نامعتبر برای {symbol}: {type(data)}")
                return None
                
        except Exception as e:
            logger.error(f"خطا در پردازش داده‌های {symbol}: {e}")
            return None
    
    @staticmethod
    def convert_list_to_dict(data_list: List, symbol: str) -> List[Dict]:
        """تبدیل لیست به دیکشنری"""
        try:
            if not data_list or len(data_list) == 0:
                return []
            
            first_item = data_list[0]
            
            # اگر لیست از لیست‌ها است (مثل داده‌های Binance)
            if isinstance(first_item, (list, tuple)):
                formatted_data = []
                for item in data_list:
                    if len(item) >= 6:
                        formatted_data.append({
                            'timestamp': item[0],
                            'open': float(item[1]),
                            'high': float(item[2]),
                            'low': float(item[3]),
                            'close': float(item[4]),
                            'volume': float(item[5]),
                            'symbol': symbol
                        })
                return formatted_data
            
            return data_list
            
        except Exception as e:
            logger.error(f"خطا در تبدیل لیست به دیکشنری برای {symbol}: {e}")
            return []

class TradingStrategy:
    """استراتژی معاملاتی"""
    
    def __init__(self):
        self.name = "TrendFollowingStrategy"
    
    def calculate_sma(self, prices: List[float], window: int) -> List[float]:
        """محاسبه میانگین متحرک ساده"""
        if len(prices) < window:
            return [None] * len(prices)
        
        return pd.Series(prices).rolling(window=window).mean().tolist()
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """محاسبه RSI"""
        if len(prices) < period + 1:
            return [50] * len(prices)
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gains = []
        avg_losses = []
        rsi_values = []
        
        # محاسبه اولیه
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        for i in range(len(prices)):
            if i < period:
                rsi_values.append(50)
                continue
            
            avg_gain = (avg_gain * (period - 1) + gains[i-1]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i-1]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values

    def generate_signals(self, symbol: str, market_data: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        تابع generate_signals با رفع خطای اصلی
        """
        try:
            # بررسی وجود داده
            if not market_data or len(market_data) < 20:
                logger.warning(f"داده‌های ناکافی برای تولید سیگنال {symbol}")
                return None
            
            logger.info(f"تولید سیگنال برای {symbol} با {len(market_data)} داده")
            
            # استخراج قیمت‌ها
            closes = [candle['close'] for candle in market_data]
            highs = [candle['high'] for candle in market_data]
            lows = [candle['low'] for candle in market_data]
            
            # محاسبه اندیکاتورها
            sma_20 = self.calculate_sma(closes, 20)
            sma_50 = self.calculate_sma(closes, 50)
            rsi = self.calculate_rsi(closes, 14)
            
            # دریافت آخرین مقادیر
            current_close = closes[-1]
            current_sma_20 = sma_20[-1] if sma_20[-1] is not None else current_close
            current_sma_50 = sma_50[-1] if sma_50[-1] is not None else current_close
            current_rsi = rsi[-1] if rsi else 50
            
            # منطق سیگنال‌دهی
            signal = "HOLD"
            reason = ""
            
            if current_sma_20 > current_sma_50 and current_rsi < 70:
                signal = "BUY"
                reason = "روند صعودی و RSI مناسب"
            elif current_sma_20 < current_sma_50 and current_rsi > 30:
                signal = "SELL"
                reason = "روند نزولی و RSI مناسب"
            elif current_rsi > 80:
                signal = "SELL"
                reason = "اشباع خرید"
            elif current_rsi < 20:
                signal = "BUY"
                reason = "اشباع فروش"
            
            # ایجاد سیگنال
            signal_data = {
                'symbol': symbol,
                'signal': signal,
                'price': current_close,
                'sma_20': current_sma_20,
                'sma_50': current_sma_50,
                'rsi': round(current_rsi, 2),
                'timestamp': market_data[-1]['timestamp'],
                'reason': reason,
                'confidence': self.calculate_confidence(current_rsi, current_sma_20, current_sma_50)
            }
            
            logger.info(f"سیگنال تولید شده برای {symbol}: {signal}")
            return signal_data
            
        except Exception as e:
            logger.error(f"خطا در generate_signals برای {symbol}: {e}")
            logger.exception("جزییات خطا:")
            return None
    
    def calculate_confidence(self, rsi: float, sma_20: float, sma_50: float) -> float:
        """محاسبه میزان اطمینان از سیگنال"""
        confidence = 0.5
        
        # اعتماد بر اساس RSI
        if rsi < 20 or rsi > 80:
            confidence += 0.3
        elif 30 <= rsi <= 70:
            confidence += 0.1
        
        # اعتماد بر اساس تقاطع میانگین‌ها
        sma_diff = abs(sma_20 - sma_50) / sma_50
        if sma_diff > 0.05:  # تفاوت بیش از 5%
            confidence += 0.2
        
        return min(confidence, 0.95)  # حداکثر 95% اطمینان

class StrategyExecutor:
    """اجراکننده اصلی استراتژی"""
    
    def __init__(self):
        self.data_fetcher = CryptoDataFetcher()
        self.data_processor = DataProcessor()
        self.strategy = TradingStrategy()
        self.symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "XRPUSDT"]
    
    def analyze_symbol(self, symbol: str) -> Optional[Dict]:
        """تحلیل یک نماد"""
        logger.info(f"Analyzing {symbol}...")
        
        try:
            # دریافت داده خام
            raw_data = self.data_fetcher.fetch_data(symbol, "binance", interval="1h", limit=100)
            
            # پردازش و اعتبارسنجی داده‌ها
            processed_data = self.data_processor.safe_data_access(raw_data, symbol)
            
            if processed_data is None:
                logger.warning(f"داده‌های {symbol} برای پردازش نامعتبر است")
                return None
            
            # تولید سیگنال
            signal = self.strategy.generate_signals(symbol, processed_data)
            return signal
            
        except Exception as e:
            logger.error(f"خطا در تحلیل {symbol}: {e}")
            return None
    
    def run_analysis(self):
        """اجرای تحلیل برای تمام نمادها"""
        results = {}
        
        for symbol in self.symbols:
            signal = self.analyze_symbol(symbol)
            if signal:
                results[symbol] = signal
                logger.info(f"تحلیل {symbol} با موفقیت انجام شد")
            else:
                logger.warning(f"تحلیل {symbol} ناموفق بود")
            
            # تاخیر برای جلوگیری از Rate Limit
            time.sleep(0.5)
        
        return results

def main():
    """تابع اصلی"""
    try:
        print("🤖 ربات سیگنال‌یابی در حال راه‌اندازی...")
        
        executor = StrategyExecutor()
        results = executor.run_analysis()
        
        print("\n" + "="*60)
        print("نتایج تحلیل سیگنال‌ها:")
        print("="*60)
        
        for symbol, signal in results.items():
            print(f"{symbol}: {signal['signal']} - قیمت: {signal['price']:.2f}")
            print(f"   RSI: {signal['rsi']} - اطمینان: {signal['confidence']:.0%}")
            print(f"   دلیل: {signal['reason']}")
            print("-" * 40)
        
        print(f"✅ تحلیل با موفقیت انجام شد. تعداد سیگنال‌ها: {len(results)}")
        
    except Exception as e:
        print(f"💥 خطای غیرمنتظره: {e}")
        logger.exception("خطای جزئی:")

if __name__ == "__main__":
    main()
