import pytest
import pandas as pd
import numpy as np
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from strategies.mutanabby_strategy import MutanabbyStrategy

class TestMutanabbyStrategy:
    
    @pytest.fixture
    def strategy(self):
        return MutanabbyStrategy()
    
    @pytest.fixture
    def sample_data(self):
        """ایجاد داده نمونه برای تست"""
        dates = pd.date_range('2023-01-01', periods=100, freq='15min')
        data = pd.DataFrame({
            'open': np.random.uniform(28000, 32000, 100),
            'high': np.random.uniform(28500, 32500, 100),
            'low': np.random.uniform(27500, 31500, 100),
            'close': np.random.uniform(28000, 32000, 100),
            'volume': np.random.uniform(1000, 5000, 100)
        }, index=dates)
        return data
    
    def test_calculate_ema(self, strategy, sample_data):
        """تست محاسبه EMA"""
        ema_20 = strategy.calculate_ema(sample_data, 20)
        
        assert len(ema_20) == len(sample_data)
        assert not ema_20.isnull().all()
    
    def test_calculate_atr(self, strategy, sample_data):
        """تست محاسبه ATR"""
        atr = strategy.calculate_atr(sample_data, 14)
        
        assert len(atr) == len(sample_data)
        assert atr.iloc[-1] > 0  # ATR should be positive
    
    def test_calculate_macd(self, strategy, sample_data):
        """تست محاسبه MACD"""
        macd, signal, hist = strategy.calculate_macd(sample_data)
        
        assert len(macd) == len(sample_data)
        assert len(signal) == len(sample_data)
        assert len(hist) == len(sample_data)
    
    def test_generate_signals_no_data(self, strategy):
        """تست تولید سیگنال با داده ناکافی"""
        empty_data = pd.DataFrame()
        signals = strategy.generate_signals(empty_data)
        
        assert signals == []
    
    def test_generate_signals_with_data(self, strategy, sample_data):
        """تست تولید سیگنال با داده کافی"""
        signals = strategy.generate_signals(sample_data)
        
        assert isinstance(signals, list)
        # ممکن است سیگنالی پیدا شود یا نه، اما باید لیست باشد

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
