# src/strategy_engine.py
import pandas as pd
import numpy as np
from typing import Dict
import config

class InstitutionalStrategy:
    def __init__(self):
        params = config.STRATEGY_PARAMS
        self.short_ema = params["short_ema"]
        self.long_ema = params["long_ema"]
        self.rsi_period = params["rsi_period"]
        self.rsi_buy = params["rsi_buy"]
        self.rsi_sell = params["rsi_sell"]
        self.vol_lookback = params["vol_lookback"]
        self.vol_std_mult = params["vol_std_mult"]
        self.atr_mult_sl = params["atr_mult_sl"]
        self.atr_mult_tp = params["atr_mult_tp"]

        self.filter_stats = {
            "ema_crossover": 0,
            "rsi_filter": 0,
            "volume_filter": 0,
            "total_signals": 0
        }

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()

        # 1. EMA (20 و 50)
        data['ema_short'] = data['close'].ewm(span=self.short_ema).mean()
        data['ema_long'] = data['close'].ewm(span=self.long_ema).mean()
        ema_bullish = data['ema_short'] > data['ema_long']

        # 2. RSI (14)
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        rsi_oversold = data['rsi'] < self.rsi_buy

        # 3. Volume Spike
        data['vol_mean'] = data['volume'].rolling(self.vol_lookback).mean()
        data['vol_std'] = data['volume'].rolling(self.vol_lookback).std()
        volume_spike = data['volume'] > (data['vol_mean'] + self.vol_std_mult * data['vol_std'])

        # 4. ATR (14) - True Range
        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data['atr'] = tr.rolling(14).mean()

        # مدیریت ریسک
        data['stop_loss'] = data['close'] - data['atr'] * self.atr_mult_sl
        data['take_profit'] = data['close'] + data['atr'] * self.atr_mult_tp

        # ترکیب فیلترها
        buy_signal = ema_bullish & rsi_oversold & volume_spike
        data['signal'] = np.where(buy_signal, 1, 0)

        # آمار فیلترها
        self.filter_stats["ema_crossover"] = buy_signal.sum()
        self.filter_stats["rsi_filter"] = (buy_signal & rsi_oversold).sum()
        self.filter_stats["volume_filter"] = (buy_signal & volume_spike).sum()
        self.filter_stats["total_signals"] = buy_signal.sum()

        return data

    def get_filter_stats(self
