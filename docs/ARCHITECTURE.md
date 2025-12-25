# Kite Paper Trading Bot - Architecture & Code Documentation

> **Version:** 2.0.0  
> **Last Updated:** December 2025

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [Strategies](#strategies)
6. [Data Sources](#data-sources)
7. [Registry System](#registry-system)
8. [Configuration](#configuration)
9. [Extending the Bot](#extending-the-bot)

---

## Overview

The Kite Paper Trading Bot is a modular, extensible trading bot framework for backtesting and paper trading Indian market instruments. It supports multiple trading strategies and data sources through a plugin-based architecture.

### Key Features

- **Modular Architecture**: Easily add new strategies and data sources
- **Paper Trading**: Simulate trades without risking real money
- **Backtesting**: Test strategies against historical data
- **Live Mode**: Run strategies with real-time market data
- **Risk Management**: Built-in stop-loss and take-profit mechanisms
- **Free Data**: Uses Yahoo Finance (no API key required)
- **Paid Data**: Optional Kite Connect integration for premium data

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           main.py                                │
│                    (Entry Point & Orchestrator)                  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   Registry    │    │   Backtester  │    │  Paper Broker │
│   (Factory)   │    │               │    │               │
└───────┬───────┘    └───────────────┘    └───────────────┘
        │
   ┌────┴────┐
   │         │
   ▼         ▼
┌──────┐  ┌──────┐
│Strat-│  │ Data │
│egies │  │Source│
└──────┘  └──────┘
```

### Component Relationships

```
┌─────────────────────┐     ┌─────────────────────┐
│   StrategyRegistry  │     │  DataSourceRegistry │
│  ┌───────────────┐  │     │  ┌───────────────┐  │
│  │ register()    │  │     │  │ register()    │  │
│  │ get()         │  │     │  │ get()         │  │
│  │ create()      │  │     │  │ create()      │  │
│  │ list_all()    │  │     │  │ list_all()    │  │
│  └───────────────┘  │     │  └───────────────┘  │
└─────────┬───────────┘     └─────────┬───────────┘
          │                           │
    ┌─────┴─────┐               ┌─────┴─────┐
    ▼           ▼               ▼           ▼
┌────────┐  ┌────────┐    ┌────────┐  ┌────────┐
│  SMA   │  │ Future │    │ Yahoo  │  │  Kite  │
│Crossover│  │Strategy│    │Finance │  │Connect │
└────────┘  └────────┘    └────────┘  └────────┘
     │           │              │           │
     └─────┬─────┘              └─────┬─────┘
           │                          │
           ▼                          ▼
    ┌────────────┐            ┌────────────┐
    │BaseStrategy│            │BaseDataSrc │
    │  (ABC)     │            │   (ABC)    │
    └────────────┘            └────────────┘
```

### Data Flow

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Data Source  │───▶│   Strategy   │───▶│    Broker    │
│ (OHLCV Data) │    │  (Signals)   │    │   (Trades)   │
└──────────────┘    └──────────────┘    └──────────────┘
       │                   │                    │
       │                   │                    │
       ▼                   ▼                    ▼
   DataFrame          BUY/SELL/HOLD      Balance/Positions
```

---

## Project Structure

```
kite-paper-trading-bot/
├── .env                      # Configuration (API keys, settings)
├── requirements.txt          # Python dependencies
├── README.md                 # Project overview & run instructions
│
├── docs/                     # Documentation
│   ├── ARCHITECTURE.md       # This file
│   ├── QUICKSTART.md         # Getting started guide
│   └── strategies.txt        # Strategy explanations
│
├── logs/                     # Trade and bot logs (root level)
│   ├── backtest_trades_log.csv
│   ├── kite_bot.log
│   └── trades_log.csv
│
└── src/
    ├── __init__.py
    ├── main.py               # Entry point & CLI argument parsing
    │
    ├── core/                 # Core engine modules
    │   ├── __init__.py
    │   ├── backtester.py     # Backtesting engine
    │   └── registry.py       # Strategy & DataSource registries
    │
    ├── broker/
    │   ├── __init__.py
    │   ├── paper.py          # Paper trading broker
    │   └── kite.py           # Kite Connect broker
    │
    ├── data/
    │   ├── __init__.py
    │   ├── base.py           # BaseDataSource ABC
    │   ├── data_manager.py   # Smart data caching
    │   ├── download_data.py  # Manual data download utility
    │   ├── kite.py           # Kite Connect data source
    │   ├── yahoo.py          # Yahoo Finance data source (free)
    │   ├── data_metadata.json    # Data freshness tracking
    │   └── historical_prices.csv # Cached price data
    │
    ├── strategy/
    │   ├── __init__.py
    │   ├── base.py           # BaseStrategy ABC
    │   └── sma_crossover.py  # SMA Crossover implementation
    │
    └── utils/
        ├── __init__.py
        └── logger.py         # Centralized logging
```

---

## Core Components

### 1. main.py - Entry Point

The main orchestrator that:
- Loads configuration from `.env`
- Parses command-line arguments (with .env as defaults)
- Initializes the registry system
- Creates strategy and data source instances
- Runs in BACKTEST or LIVE mode

```python
# Key responsibilities:
- Parse CLI arguments (--mode, --strategy, --fast, --slow, etc.)
- Load environment variables as defaults
- Initialize strategy via registry
- Initialize data source via registry
- Run backtest or live trading loop
- Handle stop-loss/take-profit
- Log trades to CSV
```

### 2. core/backtester.py - Backtesting Engine

Runs strategies against historical data:

```python
def backtest(
    df: pd.DataFrame,           # Historical OHLCV data
    strategy: BaseStrategy,     # Strategy instance
    initial_balance: float,     # Starting capital
    symbol: str,                # Trading symbol
    qty: int,                   # Quantity per trade
    stop_loss_percent: float,   # Stop-loss threshold
    take_profit_percent: float  # Take-profit threshold
) -> PaperBroker:
    """Run backtest and return broker with results"""
```

### 3. PaperBroker - Trade Simulation

Simulates trading without real money:

```python
class PaperBroker:
    def __init__(self, initial_balance: float)
    def buy(self, symbol: str, price: float, qty: int) -> bool
    def sell(self, symbol: str, price: float) -> float  # Returns PnL
    
    # Properties
    balance: float           # Current cash balance
    positions: dict          # Open positions {symbol: {qty, avg_price}}
```

---

## Strategies

### BaseStrategy (Abstract Base Class)

All strategies must inherit from `BaseStrategy`:

```python
from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    # Class attributes (override in subclass)
    name: str = "base"
    description: str = "Base Strategy"
    version: str = "1.0.0"
    
    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> str:
        """
        Generate trading signal from OHLCV data.
        
        Returns: "BUY", "SELL", or "HOLD"
        """
        pass
    
    def get_required_periods(self) -> int:
        """Minimum data points needed for signal generation"""
        return 1
    
    def get_parameters(self) -> dict:
        """Return current strategy parameters"""
        return {}
    
    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """Validate DataFrame has required columns"""
        pass
    
    def record_signal(self, signal: str):
        """Record signal to history"""
        pass
    
    def get_signal_history(self) -> list:
        """Get all recorded signals"""
        pass
```

### SMACrossoverStrategy

Simple Moving Average Crossover implementation:

```python
class SMACrossoverStrategy(BaseStrategy):
    name = "sma_crossover"
    description = "Simple Moving Average Crossover Strategy"
    version = "2.0.0"
    
    def __init__(self, fast_period: int = 5, slow_period: int = 20):
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signal(self, df: pd.DataFrame) -> str:
        # Calculate SMAs
        df["fast"] = df["close"].rolling(self.fast_period).mean()
        df["slow"] = df["close"].rolling(self.slow_period).mean()
        
        # Detect crossover
        if fast_crosses_above_slow:
            return "BUY"
        elif fast_crosses_below_slow:
            return "SELL"
        return "HOLD"
```

**Signal Logic:**
- **BUY**: Fast SMA crosses above Slow SMA (bullish crossover)
- **SELL**: Fast SMA crosses below Slow SMA (bearish crossover)
- **HOLD**: No crossover detected

---

## Data Sources

### BaseDataSource (Abstract Base Class)

All data sources must inherit from `BaseDataSource`:

```python
from abc import ABC, abstractmethod
import pandas as pd

class BaseDataSource(ABC):
    # Class attributes
    name: str = "base"
    description: str = "Base Data Source"
    requires_auth: bool = False
    
    @abstractmethod
    def connect(self, **credentials) -> bool:
        """Establish connection to data source"""
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
        
        Returns: DataFrame with columns:
            date, open, high, low, close, volume
        """
        pass
    
    @abstractmethod
    def get_live_price(self, symbol: str) -> float:
        """Get current price for symbol"""
        pass
    
    @staticmethod
    def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to standard format"""
        pass
```

### YahooFinanceDataSource

Free data source using Yahoo Finance:

```python
class YahooFinanceDataSource(BaseDataSource):
    name = "yahoo"
    description = "Yahoo Finance (Free)"
    requires_auth = False
    
    # Symbol mapping
    SYMBOL_MAP = {
        "NIFTY": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "RELIANCE": "RELIANCE.NS",
        # ... more symbols
    }
    
    def connect(self, **credentials) -> bool:
        # No authentication needed
        return True
    
    def get_historical_data(self, symbol, interval, days):
        # Uses yfinance library
        ticker = yf.Ticker(yahoo_symbol)
        return ticker.history(...)
```

### KiteDataSource

Premium data source using Zerodha's Kite Connect:

```python
class KiteDataSource(BaseDataSource):
    name = "kite"
    description = "Kite Connect (Zerodha)"
    requires_auth = True
    
    def connect(self, **credentials) -> bool:
        # Requires api_key and access_token
        self._kite = KiteConnect(api_key=credentials["api_key"])
        self._kite.set_access_token(credentials["access_token"])
        return True
    
    def get_historical_data(self, symbol, interval, days):
        return self._kite.historical_data(...)
```

---

## Registry System

The registry system enables dynamic loading of strategies and data sources by name.

### StrategyRegistry

```python
class StrategyRegistry:
    _strategies: Dict[str, Type[BaseStrategy]] = {}
    
    @classmethod
    def register(cls, strategy_class: Type[BaseStrategy]):
        """Register a strategy class"""
        cls._strategies[strategy_class.name] = strategy_class
    
    @classmethod
    def get(cls, name: str) -> Type[BaseStrategy]:
        """Get strategy class by name"""
        return cls._strategies.get(name)
    
    @classmethod
    def create(cls, name: str, **params) -> BaseStrategy:
        """Create strategy instance with parameters"""
        return cls.get(name)(**params)
    
    @classmethod
    def list_all(cls) -> Dict[str, dict]:
        """List all registered strategies"""
        pass
```

### DataSourceRegistry

```python
class DataSourceRegistry:
    _sources: Dict[str, Type[BaseDataSource]] = {}
    
    @classmethod
    def register(cls, source_class: Type[BaseDataSource]):
        """Register a data source class"""
        cls._sources[source_class.name] = source_class
    
    @classmethod
    def create(cls, name: str, **credentials) -> BaseDataSource:
        """Create and connect data source"""
        source = cls.get(name)()
        source.connect(**credentials)
        return source
```

### Factory Functions

```python
def get_strategy(name: str, **params) -> BaseStrategy:
    """Factory function to get strategy by name"""
    return StrategyRegistry.create(name, **params)

def get_data_source(name: str, **credentials) -> BaseDataSource:
    """Factory function to get data source by name"""
    return DataSourceRegistry.create(name, **credentials)
```

---

## Configuration

The bot can be configured via **CLI arguments** (highest priority), **environment variables** (.env), or **built-in defaults**.

### Command-Line Arguments

```bash
python main.py [OPTIONS]
```

| Argument | Short | Description | Default |
|----------|-------|-------------|--------|
| `--mode` | `-m` | `backtest` or `live` | from .env |
| `--source` | `-s` | `free` (Yahoo) or `api` (Kite) | from .env |
| `--strategy` | | Strategy name | `sma_crossover` |
| `--fast` | | Fast SMA period | `5` |
| `--slow` | | Slow SMA period | `20` |
| `--symbol` | | Trading symbol | `NIFTY` |
| `--qty` | | Quantity per trade | `50` |
| `--balance` | | Initial balance | `1000000` |
| `--stop-loss` | | Stop-loss % (decimal) | `0.02` |
| `--take-profit` | | Take-profit % (decimal) | `0.04` |
| `--days` | | Days of historical data | `30` |
| `--interval` | | Candle interval | `5m` |
| `--refresh` | `-r` | Force data refresh | `false` |
| `--list-strategies` | | List available strategies | |
| `--list-sources` | | List available data sources | |
| `--help` | `-h` | Show help message | |

#### Examples

```bash
# Run backtest with defaults
python main.py

# Run live mode
python main.py --mode live

# Custom SMA parameters
python main.py --fast 10 --slow 30

# Different symbol and quantity
python main.py --symbol BANKNIFTY --qty 10

# Full custom configuration
python main.py --mode backtest --symbol RELIANCE --qty 100 --balance 500000

# List available strategies
python main.py --list-strategies
```

### Environment Variables (.env)

These serve as defaults when CLI arguments are not provided:

```bash
# Mode: BACKTEST or LIVE
MODE=BACKTEST

# Strategy Configuration
STRATEGY_NAME=sma_crossover
STRATEGY_FAST_PERIOD=5
STRATEGY_SLOW_PERIOD=20

# Data Source: FREE (Yahoo) or API (Kite)
DATA_SOURCE=FREE

# Trading Configuration
SYMBOL=NIFTY
QTY=25
INITIAL_BALANCE=2000000

# Risk Management
STOP_LOSS_PERCENT=0.02      # 2%
TAKE_PROFIT_PERCENT=0.04    # 4%

# Data Settings
DATA_HISTORY_DAYS=30
DATA_INTERVAL=5m
FORCE_DATA_REFRESH=false

# Kite API (if using DATA_SOURCE=API)
KITE_API_KEY=your_key
KITE_API_SECRET=your_secret
KITE_ACCESS_TOKEN=your_token
```

### Priority Order

1. **CLI arguments** (highest priority)
2. **Environment variables** (from `.env`)
3. **Built-in defaults** (lowest priority)

---

## Extending the Bot

### Adding a New Strategy

1. **Create the strategy file:**

```python
# src/strategy/rsi_strategy.py
from strategy.base import BaseStrategy
import pandas as pd

class RSIStrategy(BaseStrategy):
    name = "rsi"
    description = "Relative Strength Index Strategy"
    version = "1.0.0"
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__()
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signal(self, df: pd.DataFrame) -> str:
        if not self.validate_dataframe(df):
            return "HOLD"
        
        df = df.copy()
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < self.oversold:
            signal = "BUY"
        elif current_rsi > self.overbought:
            signal = "SELL"
        else:
            signal = "HOLD"
        
        self.record_signal(signal)
        return signal
    
    def get_required_periods(self) -> int:
        return self.period + 1
    
    def get_parameters(self) -> dict:
        return {
            "period": self.period,
            "oversold": self.oversold,
            "overbought": self.overbought
        }
```

2. **Register the strategy:**

```python
# src/registry.py
def register_all_strategies():
    from strategy.sma_crossover import SMACrossoverStrategy
    from strategy.rsi_strategy import RSIStrategy  # Add this
    
    StrategyRegistry.register(SMACrossoverStrategy)
    StrategyRegistry.register(RSIStrategy)  # Add this
```

3. **Update .env:**

```bash
STRATEGY_NAME=rsi
```

### Adding a New Data Source

1. **Create the data source file:**

```python
# src/data/alpaca_source.py
from data.base import BaseDataSource
import pandas as pd

class AlpacaDataSource(BaseDataSource):
    name = "alpaca"
    description = "Alpaca Markets API"
    requires_auth = True
    
    def connect(self, **credentials) -> bool:
        import alpaca_trade_api as tradeapi
        self._api = tradeapi.REST(
            credentials["api_key"],
            credentials["secret_key"]
        )
        self._connected = True
        return True
    
    def get_historical_data(self, symbol, interval, days):
        # Implement Alpaca-specific data fetching
        pass
    
    def get_live_price(self, symbol):
        # Implement live price fetching
        pass
```

2. **Register the data source:**

```python
# src/core/registry.py
def register_all_data_sources():
    from data.yahoo import YahooFinanceDataSource
    from data.kite import KiteDataSource
    from data.alpaca import AlpacaDataSource  # Add this
    
    DataSourceRegistry.register(YahooFinanceDataSource)
    DataSourceRegistry.register(KiteDataSource)
    DataSourceRegistry.register(AlpacaDataSource)  # Add this
```

---

## API Reference

### BaseStrategy Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `generate_signal()` | `df: DataFrame` | `str` | Generate BUY/SELL/HOLD signal |
| `get_required_periods()` | - | `int` | Minimum data points needed |
| `get_parameters()` | - | `dict` | Current strategy parameters |
| `set_parameters()` | `**kwargs` | - | Update parameters |
| `validate_dataframe()` | `df: DataFrame` | `bool` | Check DataFrame validity |
| `record_signal()` | `signal: str` | - | Add signal to history |
| `get_signal_history()` | - | `list` | Get all recorded signals |

### BaseDataSource Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `connect()` | `**credentials` | `bool` | Connect to data source |
| `disconnect()` | - | - | Disconnect from source |
| `is_connected()` | - | `bool` | Check connection status |
| `get_historical_data()` | `symbol, interval, days` | `DataFrame` | Fetch OHLCV data |
| `get_live_price()` | `symbol: str` | `float` | Get current price |
| `validate_symbol()` | `symbol: str` | `bool` | Check symbol validity |
| `normalize_dataframe()` | `df: DataFrame` | `DataFrame` | Standardize columns |

### PaperBroker Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `buy()` | `symbol, price, qty` | `bool` | Execute buy order |
| `sell()` | `symbol, price` | `float` | Execute sell, return PnL |
| `balance` | (property) | `float` | Current cash balance |
| `positions` | (property) | `dict` | Open positions |

---

## Troubleshooting

### Common Issues

1. **"Strategy not found" error**
   - Ensure strategy is registered in `registry.py`
   - Check `STRATEGY_NAME` in `.env` matches strategy's `name` attribute

2. **"No data received" warning**
   - Check internet connection
   - Verify symbol is supported by data source
   - For Kite API, ensure valid access token

3. **"Insufficient balance" warning**
   - Increase `INITIAL_BALANCE` in `.env`
   - Reduce `QTY` per trade

4. **Import errors**
   - Run from `src/` directory
   - Ensure all dependencies installed: `pip install -r requirements.txt`

---

## License

This project is for educational purposes. Use at your own risk.
