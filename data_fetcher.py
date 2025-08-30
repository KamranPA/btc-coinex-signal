# data_fetcher.py
import ccxt
import pandas as pd
from utils.logger_config import logger

def fetch_ohlcv(symbol, timeframe, limit=500):
    """
    داده OHLCV را از API عمومی صرافی CoinEx دریافت می‌کند.
    بدون نیاز به API Key یا احراز هویت.
    """
    logger.info(f"🚀 Fetching data from CoinEx (Public API) | symbol={symbol}, timeframe={timeframe}, limit={limit}")

    exchange = ccxt.coinex({
        'enableRateLimit': True,
        'options': {
            'defaultType': 'spot'  # فقط بازار اسپات
        }
    })

    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        logger.info(f"✅ Successfully fetched {len(ohlcv)} candles from CoinEx.")

        if len(ohlcv) == 0:
            logger.warning("📭 No data returned from CoinEx. Check symbol and timeframe.")
            return pd.DataFrame()

        # تبدیل به DataFrame و تنظیم زمان به صورت UTC
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
        df.set_index('timestamp', inplace=True)

        logger.debug(f"📊 Data range: {df.index[0]} to {df.index[-1]} (UTC)")
        logger.debug(f"📉 Price range: {df['close'].min():.6f} - {df['close'].max():.6f}")

        return df

    except ccxt.BadSymbol as e:
        logger.error(f"❌ Invalid symbol '{symbol}' on CoinEx. Error: {e}")
        return pd.DataFrame()
    except ccxt.NetworkError as e:
        logger.error(f"🌐 Network error while fetching data: {e}")
        return pd.DataFrame()
    except ccxt.ExchangeError as e:
        logger.error(f"💱 Exchange error: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.exception(f"💥 Unexpected error in fetch_ohlcv: {e}")
        return pd.DataFrame()
