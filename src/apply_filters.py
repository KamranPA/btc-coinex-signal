# src/apply_filters.py
import pandas as pd
import json

def evaluate_all(df):
    """
    ارزیابی تمام فیلترهای ترکیبی برای سیگنال خرید (Long) و فروش (Short)
    """
    with open('config/settings.json', 'r') as f:
        config = json.load(f)
    
    f = config['filters']
    i = len(df) - 1  # آخرین کندل
    l = df.iloc[-1]
    p = df.iloc[-2] if len(df) > 1 else None
    
    if p is None or i < 50:
        return {"long": False, "short": False, "details": {}}

    # میانگین حجم 20 کندل گذشته
    volume_avg = df['volume'].tail(20).mean()
    atr_ratio = l['atr'] / l['close']  # نوسان نسبی

    # -------------------------------
    # فیلترهای صعودی (Long)
    # -------------------------------
    long_conditions = {
        "trend_up": l['ema20'] > l['ema50'] > l['ema200'],
        "price_above_ema20": l['close'] > l['ema20'],
        "volume_spike": l['volume'] > f['min_volume_multiplier'] * volume_avg,
        "volatility_ok": atr_ratio > f['min_atr_multiplier'],
        "rsi_ok": 35 < l['rsi'] < 60,
        "bullish_candle": l['close'] > l['open'],
        "strong_body": abs(l['close'] - l['open']) / (l['high'] - l['low']) > 0.5,
        "higher_lows": l['low'] > p['low'],
        "above_vwap": l['close'] > l['vwap'],
        "rsi_divergence": False  # بعداً محاسبه می‌شود
    }

    # -------------------------------
    # فیلترهای نزولی (Short)
    # -------------------------------
    short_conditions = {
        "trend_down": l['ema20'] < l['ema50'] < l['ema200'],
        "price_below_ema20": l['close'] < l['ema20'],
        "volume_spike": l['volume'] > f['min_volume_multiplier'] * volume_avg,
        "volatility_ok": atr_ratio > f['min_atr_multiplier'],
        "rsi_ok": 40 < l['rsi'] < 65,
        "bearish_candle": l['close'] < l['open'],
        "strong_body": abs(l['close'] - l['open']) / (l['high'] - l['low']) > 0.5,
        "lower_highs": l['high'] < p['high'],
        "below_vwap": l['close'] < l['vwap'],
        "rsi_divergence": False
    }

    # محاسبه واگرایی (آخرین 5 کندل)
    if i > 5:
        recent_lows = df['low'].iloc[-5:]
        recent_highs = df['high'].iloc[-5:]
        recent_rsi = df['rsi'].iloc[-5:]

        # واگرایی صعودی (Long)
        if recent_lows.is_monotonic_increasing and not recent_rsi.is_monotonic_increasing:
            long_conditions["rsi_divergence"] = True

        # واگرایی نزولی (Short)
        if recent_highs.is_monotonic_decreasing and not recent_rsi.is_monotonic_decreasing:
            short_conditions["rsi_divergence"] = True

    # تصمیم نهایی
    long_score = sum(long_conditions.values())
    short_score = sum(short_conditions.values())

    required = config['filters']['required_filters_count']  # مثلاً 7 از 10

    result = {
        "long": long_score >= required,
        "short": short_score >= required,
        "details": {
            "long": long_conditions,
            "short": short_conditions,
            "long_score": long_score,
            "short_score": short_score,
            "required": required
        }
    }

    return result
