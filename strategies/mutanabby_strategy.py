import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MutanabbyStrategy:
    def __init__(self):
        self.name = "Mutanabby Trading Strategy"
        print("✅ استراتژی Mutanabby بارگذاری شد")
    
    def safe_data_access(self, data: Any, symbol: str = '') -> Optional[List[Dict]]:
        """
        دسترسی ایمن به داده‌ها - رفع خطای list indices must be integers or slices, not str
        """
        try:
            if data is None:
                logger.warning(f"داده‌های {symbol} None است")
                return None
            
            # اگر داده لیست است
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
                    return self.convert_list_to_dict(data, symbol)
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
                
                logger.error(f"هیچ داده لیستی در دیکشنری {symbol} یافت نشد")
                return None
            
            else:
                logger.error(f"نوع داده نامعتبر برای {symbol}: {type(data)}")
                return None
                
        except Exception as e:
            logger.error(f"خطا در پردازش داده‌های {symbol}: {e}")
            return None
    
    def convert_list_to_dict(self, data_list: List, symbol: str = '') -> List[Dict]:
        """تبدیل لیست به دیکشنری"""
        try:
            if not data_list or len(data_list) == 0:
                return []
            
            first_item = data_list[0]
            
            # اگر لیست از لیست‌ها است (فرمت استاندارد کندل)
            if isinstance(first_item, (list, tuple)) and len(first_item) >= 6:
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
    
    def generate_signals(self, market_data: Any) -> List[Dict[str, Any]]:
        """
        تولید سیگنال‌های معاملاتی - نسخه اصلاح شده
        """
        try:
            # اعتبارسنجی و پردازش داده‌ها
            processed_data = self.safe_data_access(market_data, 'unknown_symbol')
            
            if processed_data is None or len(processed_data) < 50:
                logger.warning("داده‌های ناکافی برای تولید سیگنال")
                return []
            
            # تبدیل به DataFrame برای پردازش
            df = pd.DataFrame(processed_data)
            
            # اطمینان از وجود ستون‌های ضروری
            required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    logger.error(f"ستون ضروری '{col}' در داده‌ها وجود ندارد")
                    return []
            
            # تبدیل تاریخ و تنظیم ایندکس
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # تبدیل مقادیر به عدد
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df = df.dropna()
            
            if len(df) < 50:
                logger.warning("داده‌های کافی پس از پاکسازی وجود ندارد")
                return []
            
            # محاسبه اندیکاتورها
            df = self.calculate_indicators(df)
            
            # تولید سیگنال‌ها
            signals = self.analyze_signals(df)
            
            logger.info(f"تعداد سیگنال‌های تولید شده: {len(signals)}")
            return signals
            
        except Exception as e:
            logger.error(f"خطا در generate_signals: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """محاسبه اندیکاتورهای تکنیکال"""
        try:
            # میانگین متحرک
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['sma_100'] = df['close'].rolling(window=100).mean()
            
            # RSI
            df['rsi'] = self.calculate_rsi(df['close'], 14)
            
            # MACD
            exp12 = df['close'].ewm(span=12, adjust=False).mean()
            exp26 = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = exp12 - exp26
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # بولینگر باندز
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            return df
            
        except Exception as e:
            logger.error(f"خطا در محاسبه اندیکاتورها: {e}")
            return df
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """محاسبه RSI"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([50] * len(prices), index=prices.index)
    
    def analyze_signals(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """تحلیل سیگنال‌ها بر اساس اندیکاتورها"""
        signals = []
        
        try:
            # دریافت آخرین داده
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            # شرایط خرید
            buy_conditions = [
                latest['close'] > latest['sma_20'],
                latest['sma_20'] > latest['sma_50'],
                latest['rsi'] < 40,
                latest['close'] < latest['bb_lower'],
                latest['macd'] > latest['macd_signal']
            ]
            
            # شرایط فروش
            sell_conditions = [
                latest['close'] < latest['sma_20'],
                latest['sma_20'] < latest['sma_50'],
                latest['rsi'] > 60,
                latest['close'] > latest['bb_upper'],
                latest['macd'] < latest['macd_signal']
            ]
            
            # تولید سیگنال خرید
            if sum(buy_conditions) >= 3:
                entry = latest['close']
                sl = entry * 0.95  # استاپ لاس 5%
                signals.append({
                    'type': 'BUY',
                    'entry': entry,
                    'sl': sl,
                    'tp1': entry * 1.05,  # تیک پروفیت 5%
                    'tp2': entry * 1.08,  # تیک پروفیت 8%
                    'tp3': entry * 1.12,  # تیک پروفیت 12%
                    'timestamp': latest.name,
                    'confidence': min(sum(buy_conditions) / 5 * 100, 100)
                })
            
            # تولید سیگنال فروش
            if sum(sell_conditions) >= 3:
                entry = latest['close']
                sl = entry * 1.05  # استاپ لاس 5%
                signals.append({
                    'type': 'SELL',
                    'entry': entry,
                    'sl': sl,
                    'tp1': entry * 0.95,  # تیک پروفیت 5%
                    'tp2': entry * 0.92,  # تیک پروفیت 8%
                    'tp3': entry * 0.88,  # تیک پروفیت 12%
                    'timestamp': latest.name,
                    'confidence': min(sum(sell_conditions) / 5 * 100, 100)
                })
            
        except Exception as e:
            logger.error(f"خطا در تحلیل سیگنال‌ها: {e}")
        
        return signals
