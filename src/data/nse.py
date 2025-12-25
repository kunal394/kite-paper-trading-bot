"""
NSE Data Source (FREE)

Provides free market data directly from NSE using nsetools library.
Use this as a fallback when Yahoo Finance is unavailable.

Note: nsetools provides real-time quotes but limited historical data.
For historical data, we use nsepy (if available) or fall back to other sources.
"""
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.base import BaseDataSource
from utils.logger import logger

# Try to import nsetools
try:
    from nsetools import Nse
    NSETOOLS_AVAILABLE = True
except ImportError:
    NSETOOLS_AVAILABLE = False
    logger.warning("nsetools not installed. Install with: pip install nsetools")

# Try to import nsepy for historical data
try:
    from nsepy import get_history
    NSEPY_AVAILABLE = True
except ImportError:
    NSEPY_AVAILABLE = False
    logger.warning("nsepy not installed. Install with: pip install nsepy")


class NseDataSource(BaseDataSource):
    """
    NSE data source for free Indian market data.
    
    Uses nsetools for real-time quotes and nsepy for historical data.
    Direct access to NSE - no third-party intermediary.
    
    Supported symbols:
        NIFTY, NIFTY50 → NIFTY 50 Index
        BANKNIFTY → Bank NIFTY Index
        RELIANCE, TCS, INFY, etc. → Individual stocks
    """
    
    name = "nse"
    description = "NSE Direct (Free)"
    requires_auth = False
    
    # Symbol mapping from common names to NSE symbols
    SYMBOL_MAP = {
        "NIFTY": "NIFTY 50",
        "NIFTY50": "NIFTY 50",
        "BANKNIFTY": "NIFTY BANK",
    }
    
    # Index symbols for nsepy
    INDEX_SYMBOLS = {
        "NIFTY": "NIFTY 50",
        "NIFTY50": "NIFTY 50",
        "BANKNIFTY": "NIFTY BANK",
    }
    
    def __init__(self):
        super().__init__()
        self._nse = None
        self._connected = False
    
    def connect(self, **credentials) -> bool:
        """Initialize NSE connection"""
        if not NSETOOLS_AVAILABLE:
            logger.error("nsetools not installed. Cannot use NSE data source.")
            return False
        
        try:
            self._nse = Nse()
            self._connected = True
            logger.info("NSE data source ready (no authentication required)")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize NSE connection: {e}")
            return False
    
    def _map_symbol(self, symbol: str) -> str:
        """Convert common symbol names to NSE format"""
        return self.SYMBOL_MAP.get(symbol.upper(), symbol.upper())
    
    def _is_index(self, symbol: str) -> bool:
        """Check if symbol is an index"""
        return symbol.upper() in self.INDEX_SYMBOLS
    
    def get_quote(self, symbol: str) -> dict:
        """
        Get real-time quote for a symbol.
        
        Parameters:
            symbol: Trading symbol (e.g., "RELIANCE", "TCS")
        
        Returns:
            dict with quote data including lastPrice, open, high, low, close
        """
        if not self._connected:
            self.connect()
        
        if not self._connected:
            return {}
        
        try:
            if self._is_index(symbol):
                # Get index quote
                index_name = self.INDEX_SYMBOLS.get(symbol.upper(), symbol)
                quote = self._nse.get_index_quote(index_name)
            else:
                # Get stock quote
                quote = self._nse.get_quote(symbol.upper())
            
            return quote if quote else {}
            
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return {}
    
    def get_historical_data(
        self,
        symbol: str,
        interval: str = "1day",
        days: int = 30
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from NSE.
        
        Note: nsepy only supports daily data. For intraday, use Yahoo Finance.
        
        Parameters:
            symbol: Trading symbol (e.g., "NIFTY", "RELIANCE")
            interval: Candle interval (only "1day" supported by nsepy)
            days: Number of days of history to fetch
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if not NSEPY_AVAILABLE:
            logger.error("nsepy not installed. Cannot fetch historical data from NSE.")
            return pd.DataFrame()
        
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            is_index = self._is_index(symbol)
            nse_symbol = symbol.upper()
            
            # Remove common prefixes for nsepy
            if nse_symbol in ["NIFTY", "NIFTY50"]:
                nse_symbol = "NIFTY 50"
            elif nse_symbol == "BANKNIFTY":
                nse_symbol = "NIFTY BANK"
            
            logger.info(f"Fetching {days} days of daily data for {nse_symbol} from NSE...")
            
            if is_index:
                df = get_history(
                    symbol=nse_symbol,
                    start=start_date,
                    end=end_date,
                    index=True
                )
            else:
                df = get_history(
                    symbol=nse_symbol,
                    start=start_date,
                    end=end_date
                )
            
            if df.empty:
                logger.warning(f"No historical data received for {nse_symbol}")
                return pd.DataFrame()
            
            # Format the DataFrame
            df = df.reset_index()
            df.columns = df.columns.str.lower()
            
            # Rename date column to timestamp
            if 'date' in df.columns:
                df = df.rename(columns={'date': 'timestamp'})
            
            # Keep only required columns
            available_cols = df.columns.tolist()
            required_cols = ['timestamp', 'open', 'high', 'low', 'close']
            
            # Check which columns exist
            cols_to_keep = [c for c in required_cols if c in available_cols]
            if 'volume' in available_cols:
                cols_to_keep.append('volume')
            
            df = df[cols_to_keep]
            
            logger.info(f"Downloaded {len(df)} candles from NSE")
            if not df.empty:
                logger.info(f"Date range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
                logger.info(f"Price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch NSE historical data: {e}")
            return pd.DataFrame()
    
    def get_live_price(self, symbol: str) -> float:
        """
        Get current live price for a symbol.
        
        Parameters:
            symbol: Trading symbol
        
        Returns:
            Current price as float, or 0.0 if unavailable
        """
        quote = self.get_quote(symbol)
        
        if not quote:
            return 0.0
        
        # Try different price fields
        price = quote.get('lastPrice') or quote.get('last') or quote.get('close') or 0.0
        return float(price)


def is_available() -> bool:
    """Check if NSE data source is available"""
    return NSETOOLS_AVAILABLE


def is_historical_available() -> bool:
    """Check if NSE historical data is available"""
    return NSEPY_AVAILABLE


# === Test code ===
if __name__ == "__main__":
    print("=" * 50)
    print("NSE Data Source Test")
    print("=" * 50)
    
    print(f"\nnsetools available: {NSETOOLS_AVAILABLE}")
    print(f"nsepy available: {NSEPY_AVAILABLE}")
    
    if NSETOOLS_AVAILABLE:
        source = NseDataSource()
        source.connect()
        
        # Test real-time quote
        print("\n--- Real-time Quote ---")
        quote = source.get_quote("RELIANCE")
        if quote:
            print(f"RELIANCE: ₹{quote.get('lastPrice', 'N/A')}")
        
        # Test index quote
        print("\n--- Index Quote ---")
        nifty_quote = source.get_quote("NIFTY")
        if nifty_quote:
            print(f"NIFTY 50: {nifty_quote.get('lastPrice', 'N/A')}")
    
    if NSEPY_AVAILABLE:
        print("\n--- Historical Data ---")
        source = NseDataSource()
        df = source.get_historical_data("NIFTY", days=10)
        if not df.empty:
            print(df.tail())
