# src/strategy_engine.py
import pandas as pd
import numpy as np
import talib
from typing import Dict
import config

class InstitutionalStrategy:
    def __init__(self):
        # بارگیری پارامترها از config
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

        # آمار فعال‌سازی فیلترها
        self.filter_stats = {
            "ema_crossover": 0,
            "rsi_filter": 0,
            "volume_filter": 0,
            "atr_trailing": 0,
            "total_signals": 0
        }

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """محاسبه سیگنال معاملاتی بر اساس چند فیلتر نهادی"""
        # کپی ایمن از داده
        data = df.copy()

        # 1. EMA Crossover
        data['ema_short'] = talib.EMA(data['close'], timeperiod=self.short_ema)
        data['ema_long'] = talib.EMA(data['close'], timeperiod=self.long_ema)
        ema_bullish = data['ema_short'] > data['ema_long']

        # 2. RSI Filter
        data['rsi'] = talib.RSI(data['close'], timeperiod=self.rsi_period)
        rsi_oversold = data['rsi'] < self.rsi_buy
        rsi_overbought = data['rsi'] > self.rsi_sell

        # 3. Volume Spike Detection
        data['vol_mean'] = data['volume'].rolling(self.vol_lookback).mean()
        data['vol_std'] = data['volume'].rolling(self.vol_lookback).std()
        volume_spike = data['volume'] > (data['vol_mean'] + self.vol_std_mult * data['vol_std'])

        # 4. ATR برای مدیریت ریسک
        data['atr'] = talib.ATR(data['high'], data['low'], data['close'], timeperiod=14)
        data['stop_loss'] = data['close'] - data['atr'] * self.atr_mult_sl
        data['take_profit'] = data['close'] + data['atr'] * self.atr_mult_tp

        # ترکیب فیلترها برای سیگنال خرید
        buy_signal = ema_bullish & rsi_oversold & volume_spike
        data['signal'] = np.where(buy_signal, 1, 0)

        # آمار فیلترها (فقط برای نمایش در گزارش)
        self.filter_stats["ema_crossover"] = buy_signal.sum()
        self.filter_stats["rsi_filter"] = (buy_signal & rsi_oversold).sum()
        self.filter_stats["volume_filter"] = (buy_signal & volume_spike).sum()
        self.filter_stats["total_signals"] = buy_signal.sum()

        return data

    def get_filter_stats(self) -> Dict[str, int]:
        """بازگرداندن آمار فیلترها برای گزارش"""
        return self.filter_stats.copy()

    def reset_stats(self):
        """ریست کردن آمار فیلترها در ابتدای روز جدید"""
        for k in self.filter_stats:
            self.filter_stats[k] = 0
