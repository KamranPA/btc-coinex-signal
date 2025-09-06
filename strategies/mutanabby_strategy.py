import pandas as pd
import numpy as np
from config.config import SENSITIVITY, SIGNAL_TUNER, STOP_LOSS_MULTIPLIER, RISK_REWARD_RATIOS

class MutanabbyStrategy:
    def __init__(self):
        self.sensitivity = SENSITIVITY
        self.signal_tuner = SIGNAL_TUNER
        
    def calculate_ema(self, data, period):
        return data['close'].ewm(span=period, adjust=False).mean()
    
    def calculate_atr(self, data, period=14):
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        return true_range.rolling(period).mean()
    
    def calculate_supertrend(self, data, period=10, multiplier=3):
        # محاسبه ATR
        atr = self.calculate_atr(data, period)
        
        # محاسبات سوپرترند
        hl2 = (data['high'] + data['low']) / 2
        basic_upper = hl2 + (multiplier * atr)
        basic_lower = hl2 - (multiplier * atr)
        
        # محاسبه نهایی سوپرترند
        close = data['close']
        supertrend = pd.Series(index=data.index, dtype=float)
        direction = pd.Series(index=data.index, dtype=int)
        
        for i in range(1, len(data)):
            if close.iloc[i] > basic_upper.iloc[i-1]:
                supertrend.iloc[i] = basic_lower.iloc[i]
                direction.iloc[i] = 1  # روند صعودی
            elif close.iloc[i] < basic_lower.iloc[i-1]:
                supertrend.iloc[i] = basic_upper.iloc[i]
                direction.iloc[i] = -1  # روند نزولی
            else:
                supertrend.iloc[i] = supertrend.iloc[i-1]
                direction.iloc[i] = direction.iloc[i-1]
                
                if supertrend.iloc[i] == basic_upper.iloc[i-1] and basic_upper.iloc[i] < supertrend.iloc[i]:
                    supertrend.iloc[i] = basic_upper.iloc[i]
                elif supertrend.iloc[i] == basic_upper.iloc[i-1] and basic_upper.iloc[i] >= supertrend.iloc[i]:
                    supertrend.iloc[i] = basic_upper.iloc[i]
                elif supertrend.iloc[i] == basic_lower.iloc[i-1] and basic_lower.iloc[i] > supertrend.iloc[i]:
                    supertrend.iloc[i] = basic_lower.iloc[i]
                elif supertrend.iloc[i] == basic_lower.iloc[i-1] and basic_lower.iloc[i] <= supertrend.iloc[i]:
                    supertrend.iloc[i] = basic_lower.iloc[i]
        
        return supertrend, direction
    
    def calculate_macd(self, data, fast=12, slow=26, signal=9):
        ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['close'].ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return macd, signal_line, histogram
    
    def generate_signals(self, data):
        signals = []
        
        # محاسبه اندیکاتورها
        data['ema_150'] = self.calculate_ema(data, 150)
        data['ema_250'] = self.calculate_ema(data, 250)
        data['supertrend'], data['supertrend_dir'] = self.calculate_supertrend(data, self.signal_tuner, self.sensitivity)
        data['macd'], data['macd_signal'], data['macd_hist'] = self.calculate_macd(data)
        
        # شناسایی سیگنال‌ها
        for i in range(2, len(data)):
            current = data.iloc[i]
            prev = data.iloc[i-1]
            
            # شرایط سیگنال خرید
            buy_condition = (
                current['close'] > current['supertrend'] and
                prev['close'] <= prev['supertrend'] and
                current['macd'] > current['macd_signal'] and
                current['ema_150'] > current['ema_250']
            )
            
            # شرایط سیگنال فروش
            sell_condition = (
                current['close'] < current['supertrend'] and
                prev['close'] >= prev['supertrend'] and
                current['macd'] < current['macd_signal'] and
                current['ema_150'] < current['ema_250']
            )
            
            if buy_condition:
                entry_price = current['close']
                atr = self.calculate_atr(data.iloc[:i+1]).iloc[-1]
                stop_loss = entry_price - (STOP_LOSS_MULTIPLIER * atr)
                risk_amount = entry_price - stop_loss
                
                signals.append({
                    'symbol': data['symbol'].iloc[i] if 'symbol' in data.columns else 'UNKNOWN',
                    'type': 'BUY',
                    'timestamp': data.index[i],
                    'entry': entry_price,
                    'sl': stop_loss,
                    'tp1': entry_price + (RISK_REWARD_RATIOS['TP1'] * risk_amount),
                    'tp2': entry_price + (RISK_REWARD_RATIOS['TP2'] * risk_amount),
                    'tp3': entry_price + (RISK_REWARD_RATIOS['TP3'] * risk_amount)
                })
                
            elif sell_condition:
                entry_price = current['close']
                atr = self.calculate_atr(data.iloc[:i+1]).iloc[-1]
                stop_loss = entry_price + (STOP_LOSS_MULTIPLIER * atr)
                risk_amount = stop_loss - entry_price
                
                signals.append({
                    'symbol': data['symbol'].iloc[i] if 'symbol' in data.columns else 'UNKNOWN',
                    'type': 'SELL',
                    'timestamp': data.index[i],
                    'entry': entry_price,
                    'sl': stop_loss,
                    'tp1': entry_price - (RISK_REWARD_RATIOS['TP1'] * risk_amount),
                    'tp2': entry_price - (RISK_REWARD_RATIOS['TP2'] * risk_amount),
                    'tp3': entry_price - (RISK_REWARD_RATIOS['TP3'] * risk_amount)
                })
        
        return signals
