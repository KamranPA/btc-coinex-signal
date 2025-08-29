import pandas as pd

def detect_market_regime(df, window=20):
    """
    تشخیص نوع بازار: روندی (Trending) یا رنج (Ranging)
    با استفاده از ADX و Kumo (ایچیموکو)
    """
    # ADX از ta-lib
    from ta.trend import ADXIndicator
    adx = ADXIndicator(df['high'], df['low'], df['close'], window=window)
    df['adx'] = adx.adx()

    # Kumo Thickness (قدرت ابر)
    df['kumo_top'] = (df['senkou_span_a'] + df['senkou_span_b']) / 2
    df['kumo_thickness'] = abs(df['senkou_span_a'] - df['senkou_span_b'])

    # تصمیم‌گیری
    df['regime'] = 'Ranging'
    df.loc[df['adx'] > 25, 'regime'] = 'Trending'
    return df
