"""
Data Module

Contains data sources for fetching market data.

Available Sources:
- YahooFinanceDataSource: Free data via Yahoo Finance (supports intraday)
- NseDataSource: Free data directly from NSE (daily data, real-time quotes)
- KiteDataSource: Paid data via Kite Connect API
"""
from data.base import BaseDataSource
from data.yahoo import YahooFinanceDataSource
from data.kite import KiteDataSource

# Import NSE source if available
try:
    from data.nse import NseDataSource, is_available as nse_available
    NSE_AVAILABLE = nse_available()
except ImportError:
    NseDataSource = None
    NSE_AVAILABLE = False

__all__ = [
    "BaseDataSource",
    "YahooFinanceDataSource",
    "KiteDataSource",
    "NseDataSource",
    "NSE_AVAILABLE",
]
