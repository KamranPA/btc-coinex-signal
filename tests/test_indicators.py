import unittest
import pandas as pd
from src.indicators.rsi_divergence import detect_rsi_momentum_divergence
from src.indicators.ichimoku import calculate_ichimoku

class TestIndicators(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [102, 103, 104, 105, 106],
            'low': [98, 99, 100, 101, 102],
            'close': [101, 102, 103, 104, 105],
            'volume': [1000, 1200, 1100, 1300, 1400]
        })

    def test_rsi_divergence_runs(self):
        bullish, bearish = detect_rsi_momentum_divergence(self.df)
        self.assertIsInstance(bullish, list)
        self.assertIsInstance(bearish, list)

    def test_ichimoku_runs(self):
        df = calculate_ichimoku(self.df)
        self.assertIn('tenkan_sen', df.columns)
        self.assertIn('kijun_sen', df.columns)

if __name__ == '__main__':
    unittest.main()
