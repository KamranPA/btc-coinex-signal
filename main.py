import time
import pandas as pd
import numpy as np
from services.coinex_api import CoinExAPI
from services.telegram_bot import TelegramBot
from strategies.mutanabby_strategy import MutanabbyStrategy
from config.config import SYMBOLS, TIMEFRAME
import os

def run_signal_check():
    print("Starting signal check...")
    
    coinex_api = CoinExAPI()
    telegram_bot = TelegramBot()
    strategy = MutanabbyStrategy()
    
    all_signals = []
    
    for symbol in SYMBOLS:
        try:
            print(f"Processing {symbol}...")
            
            # دریافت داده‌های بازار
            market_data = coinex_api.get_market_data(symbol, 'kline', 200, TIMEFRAME)
            
            if not market_data:
                print(f"No data received for {symbol}")
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
            all_signals.extend(signals)
            
            print(f"Found {len(signals)} signals for {symbol}")
                
        except Exception as e:
            print(f"Error processing {symbol}: {str(e)}")
    
    # ارسال همه سیگنال‌ها
    if all_signals:
        for signal in all_signals:
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
                print(f"Signal sent for {signal['symbol']}")
            else:
                print(f"Failed to send signal for {signal['symbol']}")
            
            time.sleep(1)  # تاخیر بین ارسال‌ها
    else:
        print("No signals found")
    
    print("Signal check completed")

if __name__ == "__main__":
    print("CoinEx Signal Bot started")
    run_signal_check()
