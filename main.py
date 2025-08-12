import datetime
from src import fetch_data, calc_indicators, apply_filters, calculate_risk, send_telegram

def main():
    print("در حال اجرا...")
    df = fetch_data.fetch_coinex_data()
    df = calc_indicators.add_all_indicators(df)
    filters = apply_filters.evaluate_all(df)
    latest = df.iloc[-1]
    
    if all([
        filters['trend'],
        filters['price_above_ema200'],
        filters['volume_spike'],
        filters['high_volatility'],
        filters['rsi_ok'],
        filters['structure']
    ]):
        risk = calculate_risk.calculate(df, latest['close'], "long")
        if risk['rr_ok']:
            signal = {
                'entry': round(latest['close'], 2),
                'tp': risk['tp'],
                'sl': risk['sl'],
                'risk_reward': risk['risk_reward'],
                'filters': filters,
                'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            send_telegram.send_signal(signal)
            print("✅ سیگنال ارسال شد")
        else:
            print("❌ نسبت ریسک به ریوارد کافی نیست")
    else:
        print("🟡 فیلترها تأیید نشدند")

if __name__ == "__main__":
    main()
