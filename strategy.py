# strategy.py
import pandas as pd
import numpy as np
import ta
from datetime import datetime

def apply_strategy(df, config):
    # محاسبه EMA
    df['ema150'] = ta.trend.ema_indicator(df['close'], 150)
    df['ema250'] = ta.trend.ema_indicator(df['close'], 250)
    df['hma55'] = ta.trend.hma_indicator(df['close'], 55)

    # Supertrend (باید دقیق شبیه Pine Script باشد)
    def supertrend(close, high, low, sensitivity, period):
        atr = ta.volatility.average_true_range(high, low, close, period)
        upper_band = (high + low) / 2 + sensitivity * atr
        lower_band = (high + low) / 2 - sensitivity * atr

        in_uptrend = [True] * len(close)
        for i in range(1, len(close)):
            if close[i] > upper_band[i-1]:
                in_uptrend[i] = True
            elif close[i] < lower_band[i-1]:
                in_uptrend[i] = False
            else:
                in_uptrend[i] = in_uptrend[i-1]

            if in_uptrend[i] and lower_band[i] < lower_band[i-1]:
                lower_band[i] = lower_band[i-1]
            if not in_uptrend[i] and upper_band[i] > upper_band[i-1]:
                upper_band[i] = upper_band[i-1]

        return in_uptrend, upper_band, lower_band

    in_uptrend, supertrend_upper, supertrend_lower = supertrend(
        df['close'], df['high'], df['low'], config.SENSITIVITY, config.STUNER
    )
    df['supertrend'] = np.where(in_uptrend, supertrend_lower, supertrend_upper)
    df['supertrend_up'] = in_uptrend

    # MACD
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_hist'] = macd.macd_diff()

    # DMI/ADX (برای تشخیص روند)
    dmi = ta.trend.ADIIndicator(df['high'], df['low'], df['close'])
    df['adx'] = ta.trend.adx(df['high'], df['low'], df['close'], 14)

    # WaveTrend (ساده‌شده)
    def wavetrend(src, chl_len, avg_len):
        esa = src.ewm(span=chl_len).mean()
        d = np.abs(src - esa).ewm(span=chl_len).mean()
        ci = (src - esa) / (0.015 * d)
        wt1 = ci.ewm(span=avg_len).mean()
        wt2 = wt1.rolling(3).mean()
        return wt1, wt2

    wt1, wt2 = wavetrend(df['close'], 5 * config.MSTUNER, 10 * config.MSTUNER)
    df['wt1'] = wt1
    df['wt2'] = wt2

    # تشخیص سیگنال خرید/فروش (مطابق Pine Script)
    crossover = (df['close'] > df['supertrend']) & (df['close'].shift(1) <= df['supertrend'].shift(1))
    crossunder = (df['close'] < df['supertrend']) & (df['close'].shift(1) >= df['supertrend'].shift(1))

    df['confBull'] = (
        crossover |
        ((crossover.shift(1)) & (df['macd'] > 0) & (df['macd'] > df['macd'].shift(1)) &
         (df['ema150'] > df['ema250']) & (df['hma55'] > df['hma55'].shift(2)) & (df['adx'] > 20))
    )

    df['confBear'] = (
        crossunder |
        ((crossunder.shift(1)) & (df['macd'] < 0) & (df['macd'] < df['macd'].shift(1)) &
         (df['ema150'] < df['ema250']) & (df['hma55'] < df['hma55'].shift(2)) & (df['adx'] > 20))
    )

    # فیلترهای اضافی (مثلاً Strong Filter)
    strong_filter = ta.trend.ema_indicator(df['close'], 200)
    df['bull_signal'] = df['confBull'] & (df['close'] > strong_filter)
    df['bear_signal'] = df['confBear'] & (df['close'] < strong_filter)

    return df
