"""
Strategy Module

Contains trading strategies that generate buy/sell signals.
"""
from strategy.base import BaseStrategy
from strategy.sma_crossover import SMACrossoverStrategy

__all__ = [
    "BaseStrategy",
    "SMACrossoverStrategy",
]
