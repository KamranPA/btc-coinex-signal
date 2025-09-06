import time
import schedule
from datetime import datetime
from services.coinex_api import CoinExAPI
from services.telegram_bot import TelegramBot
from strategies.mutanabby_strategy import MutanabbyStrategy
from config.config import SYMBOLS, TIMEFRAME
from utils.logger import setup_logger

logger = setup_logger()

def run_signal_check():
    logger.info("Starting signal check...")
    
    coinex_api = CoinExAPI()
    telegram_bot = TelegramBot()
    strategy = MutanabbyStrategy()
    
    for symbol in SYMBOLS:
        try:
            # دریافت داده‌های بازار
            market_data = coinex_api.get_market_data(symbol, 'kline', 200, TIMEFRAME)
            
            if not market_data:
                logger.warning(f"No data received for {symbol}")
                continue
            
            # تبدیل به DataFrame
            df = pd.DataFrame(market_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df.set_index('timestamp', inplace=True)
            df['symbol'] = symbol
            
            # تبدیل مقادیر به عدد
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            # تولید سیگنال‌ها
            signals = strategy.generate_signals(df)
            
            # ارسال سیگنال‌های جدید
            for signal in signals:
                message = telegram_bot.format_signal_message(
                    symbol=signal['symbol'],
                    signal_type='خرید' if signal['type'] == 'BUY' else 'فروش',
                    entry=round(signal['entry'], 4),
                    sl=round(signal['sl'], 4),
                    tp1=round(signal['tp1'], 4),
                    tp2=round(signal['tp2'], 4),
                    tp3=round(signal['tp3'], 4)
                )
                
                if telegram_bot.send_message(message):
                    logger.info(f"Signal sent for {symbol}")
                else:
                    logger.error(f"Failed to send signal for {symbol}")
                
                # تاخیر بین ارسال سیگنال‌ها
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error processing {symbol}: {str(e)}")
    
    logger.info("Signal check completed")

if __name__ == "__main__":
    logger.info("CoinEx Signal Bot started")
    
    # اجرای اولیه
    run_signal_check()
    
    # برنامه‌ریزی اجرای هر ۱۵ دقیقه
    schedule.every(15).minutes.do(run_signal_check)
    
    while True:
        schedule.run_pending()
        time.sleep(1)
