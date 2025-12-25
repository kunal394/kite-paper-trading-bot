"""
Registry System for Strategies and Data Sources

Provides a centralized way to register, discover, and instantiate
strategies and data sources by name.
"""
import sys
import os
from typing import Dict, Type, Optional, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.base import BaseStrategy
from data.base import BaseDataSource


class StrategyRegistry:
    """
    Registry for trading strategies.
    
    Usage:
        # Register a strategy
        StrategyRegistry.register(SMACrossoverStrategy)
        
        # Get strategy by name
        strategy_class = StrategyRegistry.get("sma_crossover")
        strategy = strategy_class(fast_period=5, slow_period=20)
        
        # List all strategies
        strategies = StrategyRegistry.list_all()
    """
    
    _strategies: Dict[str, Type[BaseStrategy]] = {}
    
    @classmethod
    def register(cls, strategy_class: Type[BaseStrategy]) -> None:
        """Register a strategy class"""
        name = strategy_class.name
        cls._strategies[name] = strategy_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseStrategy]]:
        """Get a strategy class by name"""
        return cls._strategies.get(name)
    
    @classmethod
    def create(cls, name: str, **params) -> Optional[BaseStrategy]:
        """Create a strategy instance by name with parameters"""
        strategy_class = cls.get(name)
        if strategy_class:
            return strategy_class(**params)
        return None
    
    @classmethod
    def list_all(cls) -> Dict[str, dict]:
        """List all registered strategies with their info"""
        return {
            name: {
                "name": strat.name,
                "description": strat.description,
                "version": strat.version
            }
            for name, strat in cls._strategies.items()
        }
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a strategy is registered"""
        return name in cls._strategies


class DataSourceRegistry:
    """
    Registry for data sources.
    
    Usage:
        # Register a data source
        DataSourceRegistry.register(YahooFinanceDataSource)
        
        # Get data source by name
        source_class = DataSourceRegistry.get("yahoo")
        source = source_class()
        
        # List all data sources
        sources = DataSourceRegistry.list_all()
    """
    
    _sources: Dict[str, Type[BaseDataSource]] = {}
    
    @classmethod
    def register(cls, source_class: Type[BaseDataSource]) -> None:
        """Register a data source class"""
        name = source_class.name
        cls._sources[name] = source_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseDataSource]]:
        """Get a data source class by name"""
        return cls._sources.get(name)
    
    @classmethod
    def create(cls, name: str, **credentials) -> Optional[BaseDataSource]:
        """Create a data source instance and connect"""
        source_class = cls.get(name)
        if source_class:
            source = source_class()
            source.connect(**credentials)
            return source
        return None
    
    @classmethod
    def list_all(cls) -> Dict[str, dict]:
        """List all registered data sources with their info"""
        return {
            name: {
                "name": src.name,
                "description": src.description,
                "requires_auth": src.requires_auth
            }
            for name, src in cls._sources.items()
        }
    
    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a data source is registered"""
        return name in cls._sources


def register_all_strategies():
    """Auto-register all built-in strategies"""
    from strategy.sma_crossover import SMACrossoverStrategy
    StrategyRegistry.register(SMACrossoverStrategy)
    # Add more strategies here as they are created


def register_all_data_sources():
    """Auto-register all built-in data sources"""
    from data.yahoo import YahooFinanceDataSource
    from data.kite import KiteDataSource
    DataSourceRegistry.register(YahooFinanceDataSource)
    DataSourceRegistry.register(KiteDataSource)
    
    # Register NSE data source if available
    try:
        from data.nse import NseDataSource, is_available
        if is_available():
            DataSourceRegistry.register(NseDataSource)
    except ImportError:
        pass  # nsetools not installed


def initialize_registries():
    """Initialize all registries with built-in components"""
    register_all_strategies()
    register_all_data_sources()


# === Factory Functions ===

def get_strategy(name: str, **params) -> BaseStrategy:
    """
    Factory function to get a strategy by name.
    
    Parameters:
        name: Strategy name (e.g., "sma_crossover")
        **params: Strategy parameters
    
    Returns:
        Configured strategy instance
    
    Raises:
        ValueError: If strategy not found
    """
    if not StrategyRegistry.is_registered(name):
        initialize_registries()
    
    strategy = StrategyRegistry.create(name, **params)
    if strategy is None:
        available = list(StrategyRegistry.list_all().keys())
        raise ValueError(f"Strategy '{name}' not found. Available: {available}")
    
    return strategy


def get_data_source(name: str, **credentials) -> BaseDataSource:
    """
    Factory function to get a data source by name.
    
    Parameters:
        name: Data source name (e.g., "yahoo", "kite")
        **credentials: Connection credentials
    
    Returns:
        Connected data source instance
    
    Raises:
        ValueError: If data source not found
    """
    if not DataSourceRegistry.is_registered(name):
        initialize_registries()
    
    source = DataSourceRegistry.create(name, **credentials)
    if source is None:
        available = list(DataSourceRegistry.list_all().keys())
        raise ValueError(f"Data source '{name}' not found. Available: {available}")
    
    return source
