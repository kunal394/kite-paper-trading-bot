"""
SMA Crossover Strategy

A classic trend-following strategy using Simple Moving Average crossovers.
"""
import pandas as pd
from strategy.base import BaseStrategy


class SMACrossoverStrategy(BaseStrategy):
    """
    Simple Moving Average (SMA) Crossover Strategy.
    
    Generates BUY signal when fast SMA crosses above slow SMA.
    Generates SELL signal when fast SMA crosses below slow SMA.
    
    Parameters:
        fast_period (int): Period for fast SMA (default: 5)
        slow_period (int): Period for slow SMA (default: 20)
    
    Usage:
        strategy = SMACrossoverStrategy(fast_period=5, slow_period=20)
        signal = strategy.generate_signal(df)
    """
    
    name = "sma_crossover"
    description = "Simple Moving Average Crossover Strategy"
    version = "2.0.0"
    
    def __init__(self, fast_period: int = 5, slow_period: int = 20):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signal(self, df: pd.DataFrame) -> str:
        """
        Generate trading signal based on SMA crossover.
        
        Parameters:
            df: DataFrame with 'close' column
        
        Returns:
            "BUY" if fast SMA crosses above slow SMA
            "SELL" if fast SMA crosses below slow SMA
            "HOLD" otherwise
        """
        if not self.validate_dataframe(df):
            return "HOLD"
        
        # Create a copy to avoid modifying original
        df = df.copy()
        
        # Compute moving averages
        df["fast"] = df["close"].rolling(self.fast_period).mean()
        df["slow"] = df["close"].rolling(self.slow_period).mean()
        
        # Ensure we have enough data
        if len(df) < self.slow_period + 1:
            return "HOLD"
        
        # Get current and previous values
        fast_now = df["fast"].iloc[-1]
        slow_now = df["slow"].iloc[-1]
        fast_prev = df["fast"].iloc[-2]
        slow_prev = df["slow"].iloc[-2]
        
        # Check for crossover
        if fast_now > slow_now and fast_prev <= slow_prev:
            signal = "BUY"
        elif fast_now < slow_now and fast_prev >= slow_prev:
            signal = "SELL"
        else:
            signal = "HOLD"
        
        self.record_signal(signal)
        return signal
    
    def get_required_periods(self) -> int:
        """Return minimum periods needed (slow SMA period + 1 for crossover detection)"""
        return self.slow_period + 1
    
    def get_parameters(self) -> dict:
        """Return current strategy parameters"""
        return {
            "fast_period": self.fast_period,
            "slow_period": self.slow_period
        }
    
    def set_parameters(self, **kwargs):
        """Set strategy parameters with validation"""
        if "fast_period" in kwargs:
            self.fast_period = int(kwargs["fast_period"])
        if "slow_period" in kwargs:
            self.slow_period = int(kwargs["slow_period"])
        
        # Validate fast < slow
        if self.fast_period >= self.slow_period:
            raise ValueError("fast_period must be less than slow_period")


