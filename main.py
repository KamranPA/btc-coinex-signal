import datetime
from src import fetch_data, calc_indicators
from src.filters import market_structure, divergence, liquidity, volume
from src import make_decision, calculate_risk, send_telegram

def main():
    print("🚀 شروع سیستم لایو")
    df = fetch_data.fetch_data()
    df = calc_indicators.add_indicators(df)

    structure = market_structure.check_structure(df)
    div = divergence.detect_divergence(df)
    liq = liquidity.detect_liquidity_grab(df)
    vol = volume.confirm_volume(df)

    decision = make_decision.decide_entry(structure, div, liq, vol)
    l = df.iloc[-1]

    if decision["action"] != "hold":
        risk = calculate_risk.calculate_risk(df, l['close'], decision["direction"])

        final_signal = {
            **decision,
            "entry": round(l['close'], 2),
            "sl": risk["sl"],
            "tp": risk["tp"],
            "risk_reward": risk["risk_reward"],
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }

        send_telegram.send_signal(final_signal)
        print(f"✅ سیگنال {decision['direction']} ارسال شد")

if __name__ == "__main__":
    main()
