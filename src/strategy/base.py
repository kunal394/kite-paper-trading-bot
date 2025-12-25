"""
Base Strategy Class

All trading strategies should inherit from this base class.
This ensures a consistent interface for the backtester and live trading engine.
"""
from abc import ABC, abstractmethod
import pandas as pd


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    To create a new strategy:
    1. Create a new file in src/strategy/ (e.g., rsi_strategy.py)
    2. Create a class that inherits from BaseStrategy
    3. Implement the required methods: generate_signal()
    4. Register the strategy in src/strategy/__init__.py
    
    Example:
        class MyStrategy(BaseStrategy):
            name = "my_strategy"
            description = "My custom trading strategy"
            
            def __init__(self, param1=10, param2=20):
                super().__init__()
                self.param1 = param1
                self.param2 = param2
            
            def generate_signal(self, df):
                # Your logic here
                return "BUY"  # or "SELL" or "HOLD"
    """
    
    # Strategy metadata (override in subclass)
    name: str = "base_strategy"
    description: str = "Base strategy class"
    version: str = "1.0.0"
    
    def __init__(self):
        """Initialize the strategy with default parameters"""
        self._last_signal = "HOLD"
        self._signal_history = []
    
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> str:
        """
        Generate a trading signal based on the provided OHLC data.
        
        Parameters:
            df: DataFrame with columns: timestamp, open, high, low, close
                Must have at least 'close' column for most strategies.
        
        Returns:
            str: One of "BUY", "SELL", or "HOLD"
        
        Note:
            - This method should NOT modify the original DataFrame
            - Use df.copy() if you need to add columns
            - Return "HOLD" if there's not enough data
        """
        pass
    
    def get_required_periods(self) -> int:
        """
        Return the minimum number of periods needed for this strategy.
        
        Override this method to specify how much historical data
        is needed before the strategy can generate valid signals.
        
        Returns:
            int: Minimum number of candles required
        """
        return 20  # Default minimum
    
    def get_parameters(self) -> dict:
        """
        Return the current strategy parameters.
        
        Override this to expose configurable parameters.
        
        Returns:
            dict: Parameter names and their current values
        """
        return {}
    
    def set_parameters(self, **kwargs):
        """
        Set strategy parameters.
        
        Override this to allow runtime parameter adjustment.
        
        Parameters:
            **kwargs: Parameter names and values to set
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """
        Validate that the DataFrame has required columns.
        
        Parameters:
            df: DataFrame to validate
        
        Returns:
            bool: True if valid, False otherwise
        """
        required_columns = ['close']
        return all(col in df.columns for col in required_columns)
    
    def record_signal(self, signal: str):
        """Record a signal in history for analysis"""
        self._last_signal = signal
        self._signal_history.append(signal)
    
    def get_signal_history(self) -> list:
        """Get the history of generated signals"""
        return self._signal_history.copy()
    
    def reset(self):
        """Reset strategy state (useful for backtesting multiple runs)"""
        self._last_signal = "HOLD"
        self._signal_history = []
    
    def __str__(self):
        return f"{self.name} v{self.version}: {self.description}"
    
    def __repr__(self):
        return f"<Strategy: {self.name}>"
