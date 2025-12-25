"""
Base Data Source Class

Abstract base class that all data sources must inherit from.
This provides a consistent interface for fetching market data.
"""
from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd


class BaseDataSource(ABC):
    """
    Abstract base class for all data sources.
    
    All data sources (Yahoo Finance, Kite Connect, etc.) must inherit 
    from this class and implement the required methods.
    
    Attributes:
        name: Data source identifier (e.g., "yahoo", "kite")
        description: Human-readable description
        requires_auth: Whether authentication is required
    """
    
    name: str = "base"
    description: str = "Base Data Source"
    requires_auth: bool = False
    
    def __init__(self):
        """Initialize the data source"""
        self._connected = False
        self._last_error: Optional[str] = None
    
    @abstractmethod
    def connect(self, **credentials) -> bool:
        """
        Establish connection to the data source.
        
        Parameters:
            credentials: Authentication credentials (API keys, tokens, etc.)
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_historical_data(
        self,
        symbol: str,
        interval: str = "5minute",
        days: int = 30
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.
        
        Parameters:
            symbol: Trading symbol (e.g., "NIFTY 50", "RELIANCE")
            interval: Candle interval (e.g., "1minute", "5minute", "1day")
            days: Number of days of history to fetch
        
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        
        Raises:
            ConnectionError: If not connected to data source
            ValueError: If invalid symbol or interval
        """
        pass
    
    @abstractmethod
    def get_live_price(self, symbol: str) -> float:
        """
        Get current live price for a symbol.
        
        Parameters:
            symbol: Trading symbol
        
        Returns:
            Current price as float
        """
        pass
    
    def disconnect(self):
        """Disconnect from the data source"""
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check if data source is connected"""
        return self._connected
    
    def get_last_error(self) -> Optional[str]:
        """Get the last error message"""
        return self._last_error
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol is supported.
        
        Override in subclasses to add specific validation.
        
        Parameters:
            symbol: Trading symbol to validate
        
        Returns:
            True if valid, False otherwise
        """
        return bool(symbol and len(symbol) > 0)
    
    @staticmethod
    def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize DataFrame to standard format.
        
        Ensures consistent column names and types across all data sources.
        
        Parameters:
            df: Raw DataFrame from data source
        
        Returns:
            Normalized DataFrame with standard columns
        """
        if df is None or df.empty:
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        
        # Ensure lowercase column names
        df.columns = df.columns.str.lower()
        
        # Required columns
        required = ['date', 'open', 'high', 'low', 'close', 'volume']
        
        # Map common alternative names
        column_map = {
            'datetime': 'date',
            'timestamp': 'date',
            'time': 'date',
            'adj close': 'close',
            'adjusted_close': 'close'
        }
        
        for old, new in column_map.items():
            if old in df.columns and new not in df.columns:
                df = df.rename(columns={old: new})
        
        # Ensure all required columns exist
        for col in required:
            if col not in df.columns:
                if col == 'volume':
                    df[col] = 0
                else:
                    raise ValueError(f"Missing required column: {col}")
        
        return df[required]
    
    def __repr__(self):
        status = "connected" if self._connected else "disconnected"
        return f"<{self.__class__.__name__}(name='{self.name}', status='{status}')>"
