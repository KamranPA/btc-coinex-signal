def check_structure(df):
    l = df.iloc[-1]
    p = df.iloc[-2]
    pp = df.iloc[-3]

    long = (p['low'] > pp['low']) and (l['close'] > p['high'])
    short = (p['high'] < pp['high']) and (l['close'] < p['low'])

    return {"long": long, "short": short}
