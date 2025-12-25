"""
Core modules for the trading bot.

This package contains:
- backtester: Backtesting engine
- registry: Strategy and data source registries
"""

from .registry import (
    StrategyRegistry,
    DataSourceRegistry,
    get_strategy,
    get_data_source,
    initialize_registries
)

# Import backtest function
from .backtester import backtest

__all__ = [
    'backtest',
    'StrategyRegistry',
    'DataSourceRegistry',
    'get_strategy',
    'get_data_source',
    'initialize_registries'
]
