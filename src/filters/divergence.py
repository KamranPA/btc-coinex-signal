def detect_divergence(df):
    if len(df) < 5:
        return {"long": False, "short": False}

    prices_low = df['low'].tail(5)
    prices_high = df['high'].tail(5)
    rsi = df['rsi'].tail(5)

    long = prices_low.is_monotonic_decreasing and not rsi.is_monotonic_decreasing
    short = prices_high.is_monotonic_increasing and not rsi.is_monotonic_increasing

    return {"long": long, "short": short}
