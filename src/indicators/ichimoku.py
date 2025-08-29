def calculate_ichimoku(df, tenkan=9, kijun=26, senkou=52):
    """
    محاسبه تمام اجزای ایچیموکو
    """
    high_9 = df['high'].rolling(tenkan).max()
    low_9 = df['low'].rolling(tenkan).min()
    df['tenkan_sen'] = (high_9 + low_9) / 2

    high_26 = df['high'].rolling(kijun).max()
    low_26 = df['low'].rolling(kijun).min()
    df['kijun_sen'] = (high_26 + low_26) / 2

    df['senkou_span_a'] = ((df['tenkan_sen'] * 2) + (df['kijun_sen'] * 2)) / 2
    df['senkou_span_a'] = df['senkou_span_a'].shift(kijun)

    high_52 = df['high'].rolling(senkou).max()
    low_52 = df['low'].rolling(senkou).min()
    df['senkou_span_b'] = (high_52 + low_52) / 2
    df['senkou_span_b'] = df['senkou_span_b'].shift(kijun)

    df['chikou_span'] = df['close'].shift(-kijun)

    return df

def confirm_with_ichimoku(df, idx):
    """
    تأیید سیگنال واگرایی با ایچیموکو
    """
    price = df['close'].iloc[idx]
    tenkan = df['tenkan_sen'].iloc[idx]
    kijun = df['kijun_sen'].iloc[idx]
    kumo_a = df['senkou_span_a'].iloc[idx]
    kumo_b = df['senkou_span_b'].iloc[idx]

    # شرایط تأیید صعودی
    if price > max(kumo_a, kumo_b) and tenkan > kijun:
        return True
    return False
