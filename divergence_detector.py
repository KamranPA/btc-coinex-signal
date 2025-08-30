# divergence_detector.py
import numpy as np
import pandas as pd
from utils.logger_config import logger

def calculate_rsi(series, length=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=length).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
    rs = gain / loss.replace(0, 1e-10)  # جلوگیری از تقسیم بر صفر
    rsi = 100 - (100 / (1 + rs))
    return rsi

def find_pivot_low(series, left=5, right=5):
    pivot = np.full(len(series), False)
    for i in range(left, len(series) - right):
        if all(series[i] < series[i - j] for j in range(1, left + 1)) and \
           all(series[i] < series[i + j] for j in range(1, right + 1)):
            pivot[i] = True
    return pivot

def find_pivot_high(series, left=5, right=5):
    pivot = np.full(len(series), False)
    for i in range(left, len(series) - right):
        if all(series[i] > series[i - j] for j in range(1, left + 1)) and \
           all(series[i] > series[i + j] for j in range(1, right + 1)):
            pivot[i] = True
    return pivot

class DivergenceDetector:
    def __init__(self, df, rsi_length=14):
        self.df = df.copy()
        self.rsi_length = rsi_length
        self.prepare_data()

    def prepare_data(self):
        logger.info("🔧 Preparing data: calculating momentum and RSI...")
        self.df['momentum'] = self.df['close'].diff(10)
        self.df['rsi'] = calculate_rsi(self.df['momentum'], self.rsi_length)
        self.df.dropna(inplace=True)
        logger.debug(f"📊 Data prepared. Shape: {self.df.shape}")

    def detect(self):
        df = self.df
        left, right = 5, 5

        logger.info("🔍 Starting divergence detection...")
        df['pl'] = find_pivot_low(df['low'], left, right)
        df['ph'] = find_pivot_high(df['high'], left, right)

        pl_count = df['pl'].sum()
        ph_count = df['ph'].sum()
        logger.info(f"📌 Found {pl_count} pivot lows and {ph_count} pivot highs.")

        signals = []

        for i in range(right, len(df)):
            current_time = df.index[i]

            # واگرایی صعودی
            if df['pl'].iloc[i]:
                logger.debug(f"📍 [Bullish Check] Pivot Low at {current_time}: price={df['low'].iloc[i]:.6f}")
                for j in range(i - 1, max(i - 30, 0), -1):
                    if df['pl'].iloc[j]:
                        price_ll = df['low'].iloc[i] < df['low'].iloc[j]
                        rsi_hl = df['rsi'].iloc[i] > df['rsi'].iloc[j]
                        logger.debug(f"   → Compare PL[{j}] → PL[{i}]: Price LL={price_ll}, RSI HL={rsi_hl}")

                        if price_ll and rsi_hl:
                            trend_dir = 'With Trend' if df['close'].iloc[i] > df['close'].iloc[max(i-50,0)] else 'Counter-Trend'
                            signal = {
                                'type': 'Bullish',
                                'direction': trend_dir,
                                'timestamp': current_time,
                                'price': df['low'].iloc[i],
                                'rsi': df['rsi'].iloc[i],
                                'index': i,
                                'symbol': getattr(self, 'symbol', 'UNKNOWN')
                            }
                            signals.append(signal)
                            logger.info(f"✅ BULLISH DIVERGENCE DETECTED at {current_time}")
                        break

            # واگرایی نزولی
            if df['ph'].iloc[i]:
                logger.debug(f"📍 [Bearish Check] Pivot High at {current_time}: price={df['high'].iloc[i]:.6f}")
                for j in range(i - 1, max(i - 30, 0), -1):
                    if df['ph'].iloc[j]:
                        price_hh = df['high'].iloc[i] > df['high'].iloc[j]
                        rsi_lh = df['rsi'].iloc[i] < df['rsi'].iloc[j]
                        logger.debug(f"   → Compare PH[{j}] → PH[{i}]: Price HH={price_hh}, RSI LH={rsi_lh}")

                        if price_hh and rsi_lh:
                            trend_dir = 'With Trend' if df['close'].iloc[i] < df['close'].iloc[max(i-50,0)] else 'Counter-Trend'
                            signal = {
                                'type': 'Bearish',
                                'direction': trend_dir,
                                'timestamp': current_time,
                                'price': df['high'].iloc[i],
                                'rsi': df['rsi'].iloc[i],
                                'index': i,
                                'symbol': getattr(self, 'symbol', 'UNKNOWN')
                            }
                            signals.append(signal)
                            logger.info(f"✅ BEARISH DIVERGENCE DETECTED at {current_time}")
                        break

        logger.info(f"🎯 Total signals found: {len(signals)}")
        return signals
