#!/usr/bin/env python3
"""
اسکریپت دیباگ مستقل برای تست عمیق سیستم
"""

import argparse
import json
from services.debug_service import DebugService
from config.logging_config import setup_logging, get_logger

def main():
    parser = argparse.ArgumentParser(description='Debug Mode for CoinEx Signal Bot')
    parser.add_argument('--symbol', type=str, help='Specific symbol to debug')
    parser.add_argument('--comprehensive', action='store_true', help='Run comprehensive test')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # تنظیم لاگینگ
    setup_logging(debug_mode=True)
    logger = get_logger(__name__)
    
    debug_service = DebugService()
    
    if args.comprehensive:
        logger.info("Running comprehensive debug test...")
        results = debug_service.run_comprehensive_test()
        
        print("\n" + "="*50)
        print("COMPREHENSIVE DEBUG RESULTS")
        print("="*50)
        
        for symbol, result in results.items():
            status = "✅ SUCCESS" if result['status'] == 'success' else "❌ FAILED"
            print(f"{symbol}: {status}")
            if result['status'] == 'success':
                print(f"  Data points: {result['data_points']}")
                print(f"  Signals found: {result['signals_found']}")
            else:
                print(f"  Error: {result['error']}")
        
        print("="*50)
        
    elif args.symbol:
        logger.info(f"Debugging symbol: {args.symbol}")
        # دیباگ نماد خاص
        
    else:
        print("Please specify a debug mode. Use --help for options.")

if __name__ == "__main__":
    main()
