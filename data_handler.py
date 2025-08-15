# data_handler.py
import ccxt
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def fetch_kucoin_data(symbol, timeframe, limit=100, start_date=None, end_date=None):
    """
    دریافت داده از صرافی KuCoin
    """
    exchange = ccxt.kucoin({
        'options': {
            'adjustForTimezone': False
        },
        'enableRateLimit': True,
    })

    def to_timestamp(date_str):
        return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp() * 1000)

    params = {
        'limit': limit,
        'since': to_timestamp(start_date) if start_date else None
    }

    try:
        ohlcv = exchange.fetch_ohlcv(
            symbol=symbol,
            timeframe=timeframe,
            **params
        )
        if len(ohlcv) == 0:
            logger.warning(f"⚠️  داده‌ای برای {symbol} در بازه زمانی دریافت نشد.")
            return pd.DataFrame()
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        logger.info(f"✅ {len(df)} کندل دریافت شد از KuCoin برای {symbol}")
        return df
    except Exception as e:
        logger.error(f"❌ خطای دریافت داده از KuCoin: {e}")
        return pd.DataFrame()
