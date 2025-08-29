def generate_signals(df):
    df = calculate_ichimoku(df)
    df = detect_market_regime(df)
    bullish_div, bearish_div = detect_rsi_momentum_divergence(df)

    df['signal'] = 0

    for idx in bullish_div:
        if df['regime'].iloc[idx] == 'Trending':
            if confirm_with_ichimoku(df, idx):
                df['signal'].iloc[idx] = 1  # خرید

    for idx in bearish_div:
        if df['regime'].iloc[idx] == 'Trending':
            if confirm_with_ichimoku(df, idx, bearish=True):
                df['signal'].iloc[idx] = -1  # فروش

    return df
