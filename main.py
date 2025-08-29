import json
import yaml
from src.utils.data_loader import load_data_from_coinex
from src.strategy.rsi_ichimoku_strategy import generate_signals
from src.backtest.backtester import Backtester
from src.telegram.notifier import send_telegram_report
from src.utils.logger import setup_logger
def main():
    logger = setup_logger()

    # بارگذاری تنظیمات و محرمانه
    with open('config/secrets.json') as f:
        secrets = json.load(f)
    with open('config/settings.json') as f:
        settings = json.load(f)

    symbol = settings['symbol']
    timeframe = settings['timeframe']

    try:
        df = load_data_from_coinex(symbol, timeframe)
        df = generate_signals(df)
        backtester = Backtester(df)
        report = backtester.run()

        # ذخیره نتایج
        import json
        with open('results/backtest_report.json', 'w') as f:
            json.dump(report, f, indent=2)

        # ارسال به تلگرام
        send_telegram_report(report, secrets)

        logger.info("بکتست با موفقیت انجام شد و گزارش ارسال گردید.")
    except Exception as e:
        logger.error(f"خطا در اجرای سیستم: {e}")

if __name__ == "__main__":
    main()
