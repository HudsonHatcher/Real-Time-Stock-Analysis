def sma(values, period):
    out = []
    s = 0.0
    for i, v in enumerate(values):
        s += v
        if i >= period:
            s -= values[i-period]
        out.append(None if i < period-1 else round(s/period, 4))
    return out


