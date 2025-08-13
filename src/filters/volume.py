def confirm_volume(df):
    l = df.iloc[-1]
    volume_avg = df['volume'].tail(20).mean()
    return {
        "long": l['volume'] > 1.5 * volume_avg,
        "short": l['volume'] > 1.5 * volume_avg
    }
