"""
Kite Connect Data Source

Provides market data through Zerodha's Kite Connect API.
Requires paid subscription and API credentials.
"""
import datetime
import pandas as pd
from typing import Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.base import BaseDataSource
from utils.logger import logger


class KiteDataSource(BaseDataSource):
    """
    Kite Connect data source for Zerodha's trading platform.
    
    Requires:
        - Kite Connect subscription
        - API key and secret
        - Valid access token (daily login required)
    
    Features:
        - Real-time market data
        - Historical OHLCV data
        - Full instrument list
    """
    
    name = "kite"
    description = "Kite Connect (Zerodha)"
    requires_auth = True
    
    # Valid intervals for Kite
    VALID_INTERVALS = [
        "minute", "3minute", "5minute", "10minute", 
        "15minute", "30minute", "60minute", "day"
    ]
    
    def __init__(self):
        super().__init__()
        self._kite = None
    
    def connect(self, **credentials) -> bool:
        """
        Connect to Kite API.
        
        Parameters:
            api_key: Kite API key
            access_token: Valid access token
        
        OR:
            kite: Pre-configured KiteConnect instance
        """
        try:
            if "kite" in credentials:
                # Use existing KiteConnect instance
                self._kite = credentials["kite"]
                self._connected = True
                logger.info("Connected to Kite API (existing instance)")
                return True
            
            # Create new connection
            api_key = credentials.get("api_key")
            access_token = credentials.get("access_token")
            
            if not api_key or not access_token:
                self._last_error = "Missing api_key or access_token"
                return False
            
            from kiteconnect import KiteConnect
            self._kite = KiteConnect(api_key=api_key)
            self._kite.set_access_token(access_token)
            
            # Verify connection
            profile = self._kite.profile()
            logger.info(f"Connected to Kite API as {profile.get('user_name', 'Unknown')}")
            
            self._connected = True
            return True
            
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Failed to connect to Kite API: {e}")
            return False
    
    def get_historical_data(
        self,
        symbol: str,
        interval: str = "5minute",
        days: int = 30
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data from Kite.
        
        Parameters:
            symbol: Instrument token (numeric) or trading symbol
            interval: Candle interval (e.g., "5minute", "day")
            days: Number of days of history
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        if not self._connected or self._kite is None:
            self._last_error = "Not connected to Kite API"
            logger.error(self._last_error)
            return pd.DataFrame()
        
        # Validate interval
        if interval not in self.VALID_INTERVALS:
            self._last_error = f"Invalid interval: {interval}. Valid: {self.VALID_INTERVALS}"
            logger.error(self._last_error)
            return pd.DataFrame()
        
        try:
            # Convert symbol to instrument token if needed
            instrument_token = self._resolve_instrument_token(symbol)
            
            from_date = datetime.date.today() - datetime.timedelta(days=days)
            to_date = datetime.date.today()
            
            logger.info(f"Fetching {days} days of {interval} data for token {instrument_token}...")
            
            data = self._kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            
            if not data:
                self._last_error = "No data received from Kite API"
                logger.warning(self._last_error)
                return pd.DataFrame()
            
            # Convert to DataFrame and normalize
            df = pd.DataFrame(data)
            df = self.normalize_dataframe(df)
            
            logger.info(f"Fetched {len(df)} candles from Kite API")
            return df
            
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Error fetching data from Kite API: {e}")
            return pd.DataFrame()
    
    def get_live_price(self, symbol: str) -> float:
        """
        Get current live price from Kite.
        
        Parameters:
            symbol: Instrument token or trading symbol
        
        Returns:
            Last traded price
        """
        if not self._connected or self._kite is None:
            return 0.0
        
        try:
            instrument_token = self._resolve_instrument_token(symbol)
            quote = self._kite.quote(f"NSE:{symbol}")
            
            if quote:
                key = f"NSE:{symbol}"
                if key in quote:
                    return float(quote[key].get('last_price', 0))
            
            return 0.0
            
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Error fetching live price: {e}")
            return 0.0
    
    def _resolve_instrument_token(self, symbol: str) -> int:
        """
        Resolve symbol to instrument token.
        
        If symbol is already numeric, return as int.
        Otherwise, look up in instruments list.
        """
        if isinstance(symbol, int):
            return symbol
        
        if symbol.isdigit():
            return int(symbol)
        
        # TODO: Implement instrument lookup
        # For now, assume it's already an instrument token
        return int(symbol)
    
    def get_instruments(self, exchange: str = "NSE") -> list:
        """
        Get list of tradeable instruments.
        
        Parameters:
            exchange: Exchange to fetch (NSE, NFO, BSE, etc.)
        
        Returns:
            List of instrument dictionaries
        """
        if not self._connected or self._kite is None:
            return []
        
        try:
            return self._kite.instruments(exchange)
        except Exception as e:
            self._last_error = str(e)
            return []
