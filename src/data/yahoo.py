"""
Yahoo Finance Data Source (FREE)

Provides free market data using Yahoo Finance API.
Use this instead of Kite API for paper trading with real prices.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.base import BaseDataSource
from utils.logger import logger


class YahooFinanceDataSource(BaseDataSource):
    """
    Yahoo Finance data source for free market data.
    
    Provides access to historical and live market data through Yahoo Finance.
    No authentication required.
    
    Supported symbols:
        NIFTY, NIFTY50 → ^NSEI (NIFTY 50)
        BANKNIFTY → ^NSEBANK (Bank NIFTY)
        RELIANCE → RELIANCE.NS
        TCS → TCS.NS
        INFY → INFY.NS
    """
    
    name = "yahoo"
    description = "Yahoo Finance (Free)"
    requires_auth = False
    
    # Symbol mapping from common names to Yahoo Finance symbols
    SYMBOL_MAP = {
        "NIFTY": "^NSEI",
        "NIFTY50": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "RELIANCE": "RELIANCE.NS",
        "TCS": "TCS.NS",
        "INFY": "INFY.NS",
        "HDFCBANK": "HDFCBANK.NS",
        "ICICIBANK": "ICICIBANK.NS",
        "SBIN": "SBIN.NS",
    }
    
    # Interval mapping
    INTERVAL_MAP = {
        "1minute": "1m",
        "5minute": "5m",
        "15minute": "15m",
        "30minute": "30m",
        "1hour": "1h",
        "1day": "1d",
    }
    
    def __init__(self):
        super().__init__()
        self._connected = True  # Yahoo Finance doesn't require connection
    
    def connect(self, **credentials) -> bool:
        """Yahoo Finance doesn't require authentication"""
        self._connected = True
        logger.info("Yahoo Finance data source ready (no authentication required)")
        return True
    
    def _map_symbol(self, symbol: str) -> str:
        """Convert common symbol names to Yahoo Finance format"""
        return self.SYMBOL_MAP.get(symbol.upper(), symbol)
    
    def _map_interval(self, interval: str) -> str:
        """Convert interval to Yahoo Finance format"""
        return self.INTERVAL_MAP.get(interval.lower(), interval)
    
    def get_historical_data(
        self,
        symbol: str,
        interval: str = "5minute",
        days: int = 30
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from Yahoo Finance.
        
        Parameters:
            symbol: Trading symbol (e.g., "NIFTY", "RELIANCE")
            interval: Candle interval (e.g., "5minute", "1day")
            days: Number of days of history to fetch
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        yahoo_symbol = self._map_symbol(symbol)
        yahoo_interval = self._map_interval(interval)
        
        try:
            logger.info(f"Fetching {days} days of {yahoo_interval} data for {yahoo_symbol}...")
            
            ticker = yf.Ticker(yahoo_symbol)
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            df = ticker.history(start=start_date, end=end_date, interval=yahoo_interval)
            
            if df.empty:
                self._last_error = f"No data received for {yahoo_symbol}"
                logger.warning(self._last_error)
                return pd.DataFrame()
            
            # Normalize the dataframe
            df = df.reset_index()
            df = self.normalize_dataframe(df)
            
            logger.info(f"Fetched {len(df)} candles | Price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
            
            return df
            
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Error fetching data from Yahoo Finance: {e}")
            return pd.DataFrame()
    
    def get_live_price(self, symbol: str) -> float:
        """
        Get current live price from Yahoo Finance.
        
        Parameters:
            symbol: Trading symbol
        
        Returns:
            Current price as float, or 0.0 on error
        """
        yahoo_symbol = self._map_symbol(symbol)
        
        try:
            ticker = yf.Ticker(yahoo_symbol)
            # Get last 1 minute of data
            df = ticker.history(period="1d", interval="1m")
            
            if df.empty:
                return 0.0
            
            return float(df['Close'].iloc[-1])
            
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Error fetching live price: {e}")
            return 0.0
    
    def get_available_symbols(self) -> list:
        """Return list of pre-mapped symbols"""
        return list(self.SYMBOL_MAP.keys())



if __name__ == "__main__":
    # Test the class
    print("Testing Yahoo Finance data source...")
    
    source = YahooFinanceDataSource()
    print(f"Data source: {source}")
    
    df = source.get_historical_data("NIFTY", interval="5minute", days=5)
    
    if not df.empty:
        print("\nLatest NIFTY 50 data:")
        print(df[['date', 'open', 'high', 'low', 'close']].tail(10))
        
        price = source.get_live_price("NIFTY")
        print(f"\nLive NIFTY price: {price:.2f}")
