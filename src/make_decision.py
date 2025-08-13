# src/make_decision.py
import json

def decide_entry(filters_result, ml_score, df):
    """
    تصمیم نهایی بر اساس فیلترها و مدل ML
    """
    with open('config/settings.json', 'r') as f:
        config = json.load(f)

    threshold = config['ml']['threshold']  # مثلاً 0.7
    l = df.iloc[-1]

    if filters_result['long'] and ml_score >= threshold:
        return {
            "action": "buy",
            "entry": l['close'],
            "direction": "long",
            "filters": filters_result['details']['long'],
            "ml_score": round(ml_score, 2)
        }
    elif filters_result['short'] and ml_score >= threshold:
        return {
            "action": "sell",
            "entry": l['close'],
            "direction": "short",
            "filters": filters_result['details']['short'],
            "ml_score": round(ml_score, 2)
        }
    else:
        return {"action": "hold"}
