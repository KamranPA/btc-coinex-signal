import time
import pandas as pd
import numpy as np
import argparse
import sys
import os

# اضافه کردن مسیرهای پروژه به sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from services.coinex_api import CoinExAPI
    from services.telegram_bot import TelegramBot
    from services.debug_service import DebugService
    from strategies.mutanabby_strategy import MutanabbyStrategy
    from config.config import SYMBOLS, TIMEFRAME
    from config.logging_config import setup_logging, get_logger
    from utils.error_handler import error_handler
    from utils.performance_monitor import performance_monitor
except ImportError as e:
    print(f"Import error: {e}")
    print("Current working directory:", os.getcwd())
    print("Files in current directory:", os.listdir('.'))
    if os.path.exists('services'):
        print("Files in services directory:", os.listdir('services'))
    sys.exit(1)

import json

# تنظیم لاگینگ
logger = get_logger(__name__)

@error_handler.handle_error("main execution")
def run_signal_check(debug_mode=False, test_mode=False):
    """اجرای اصلی چک سیگنال"""
    
    logger.info("Starting signal check...")
    performance_monitor.start_monitoring()
    
    coinex_api = CoinExAPI()
    telegram_bot = TelegramBot()
    strategy = MutanabbyStrategy()
    debug_service = DebugService()
    
    all_signals = []
    debug_reports = {}
    
    for symbol in SYMBOLS:
        try:
            logger.info(f"Processing {symbol}...")
            
            # دریافت داده‌های بازار
            @performance_monitor.track_operation(f"get_data_{symbol}")
            @error_handler.handle_error(f"get data for {symbol}")
            def get_market_data():
                return coinex_api.get_market_data(symbol, 'kline', 300, TIMEFRAME)
            
            market_data = get_market_data()
            
            if not market_data:
                logger.warning(f"No data received for {symbol}")
                continue
            
            # پردازش داده
            @performance_monitor.track_operation(f"process_data_{symbol}")
            def process_data():
                df = pd.DataFrame(market_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                df.set_index('timestamp', inplace=True)
                df['symbol'] = symbol
                
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col])
                
                return df
            
            df = process_data()
            
            # تولید سیگنال
            @performance_monitor.track_operation(f"generate_signals_{symbol}")
            @error_handler.handle_error(f"generate signals for {symbol}")
            def generate_signals():
                return strategy.generate_signals(df)
            
            signals = generate_signals()
            all_signals.extend(signals)
            
            logger.info(f"Found {len(signals)} signals for {symbol}")
            
            # تولید گزارش دیباگ
            if debug_mode:
                @performance_monitor.track_operation(f"debug_report_{symbol}")
                def generate_debug_report():
                    return debug_service.generate_debug_report(df, signals, symbol)
                
                debug_reports[symbol] = generate_debug_report()
                logger.debug(f"Debug report generated for {symbol}")
                
        except Exception as e:
            logger.error(f"Error processing {symbol}: {str(e)}")
            continue
    
    # ارسال سیگنال‌ها (مگر در حالت تست)
    if not test_mode:
        @performance_monitor.track_operation("send_signals")
        @error_handler.handle_error("send signals")
        def send_signals():
            sent_count = 0
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
                    logger.info(f"Signal sent for {signal['symbol']}")
                    sent_count += 1
                else:
                    logger.error(f"Failed to send signal for {signal['symbol']}")
                
                time.sleep(1)  # تاخیر بین ارسال‌ها
            
            return sent_count
        
        sent_count = send_signals()
        logger.info(f"Total signals sent: {sent_count}")
    else:
        logger.info("Test mode - No signals sent")
    
    # ذخیره گزارش دیباگ
    if debug_mode and debug_reports:
        summary_file = "debug/debug_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_signals": len(all_signals),
                "reports_generated": len(debug_reports),
                "symbols_processed": list(debug_reports.keys())
            }, f, indent=2, ensure_ascii=False)
    
    # گزارش عملکرد
    performance_monitor.log_performance_report()
    
    logger.info("Signal check completed successfully")
    return {
        "total_signals": len(all_signals),
        "debug_reports": debug_reports if debug_mode else None,
        "performance_report": performance_monitor.get_performance_report()
    }

if __name__ == "__main__":
    # پارس کردن آرگومان‌های خط فرمان
    parser = argparse.ArgumentParser(description='CoinEx Signal Bot')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--test', action='store_true', help='Enable test mode (no signals sent)')
    parser.add_argument('--comprehensive-test', action='store_true', help='Run comprehensive debug test')
    
    args = parser.parse_args()
    
    # تنظیم لاگینگ
    setup_logging(debug_mode=args.debug)
    
    if args.comprehensive_test:
        logger.info("Running comprehensive debug test...")
        debug_service = DebugService()
        results = debug_service.run_comprehensive_test()
        logger.info(f"Comprehensive test completed. Results: {json.dumps(results, indent=2)}")
    else:
        # اجرای اصلی
        results = run_signal_check(debug_mode=args.debug, test_mode=args.test)
        logger.info(f"Execution completed. Found {results['total_signals']} signals")
