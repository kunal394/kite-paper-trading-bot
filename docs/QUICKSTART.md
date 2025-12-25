# Quick Start Guide

## What Was Fixed

### Critical Issues Resolved:
1. ✅ **Created missing data source** - Added Yahoo Finance implementation (`data/yahoo.py`)
2. ✅ **Fixed `.env` duplicate entries** - Removed conflicting DATA_SOURCE configurations
3. ✅ **Fixed DataFrame warnings** - Added `.copy()` to prevent SettingWithCopyWarning in strategy
4. ✅ **Fixed instrument token mapping** - Main.py now correctly uses INSTRUMENT_TOKEN for API calls
5. ✅ **Created sample historical data** - Added [historical_prices.csv](historical_prices.csv) for testing
6. ✅ **Updated requirements** - Added numpy dependency
7. ✅ **Fixed balance configuration** - Increased initial balance and adjusted QTY for realistic trading

## How to Run

### Quick Commands

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Navigate to src folder
cd src

# Run with defaults
python main.py

# Or run directly without activating venv
.venv\Scripts\python.exe src\main.py
```

### Using CLI Arguments (Recommended)

The bot supports command-line arguments that **override** `.env` settings:

```bash
# Run backtest (default)
python main.py --mode backtest

# Run live mode
python main.py --mode live

# Custom SMA parameters
python main.py --fast 10 --slow 30

# Different symbol
python main.py --symbol BANKNIFTY --qty 10

# Force data refresh
python main.py --refresh

# See all options
python main.py --help

# List available strategies
python main.py --list-strategies
```

### 1. BACKTEST Mode (No API needed):
```bash
cd src
python main.py
# OR
python main.py --mode backtest
```

The bot will:
- **Automatically fetch fresh NIFTY data** from Yahoo Finance (if needed)
- Run SMA crossover strategy on historical data
- Log all trades to `logs/backtest_trades_log.csv`
- Display final balance and positions

### 2. LIVE Mode with FREE data source:
```bash
# Using CLI (recommended)
python main.py --mode live --source free

# OR edit .env and run without args
# MODE=LIVE
# DATA_SOURCE=FREE
python main.py
```

The bot will:
- Fetch real-time data from Yahoo Finance every 5 minutes
- Execute trades based on SMA crossover signals
- Apply stop-loss (2%) and take-profit (4%) rules
- Log to `logs/trades_log.csv`

**To stop**: Create a file named `stop_bot` in the project root

### 3. LIVE Mode with Kite API:
```bash
# Using CLI
python main.py --mode live --source api

# Make sure .env has valid Kite credentials:
# KITE_API_KEY=your_api_key
# KITE_ACCESS_TOKEN=your_access_token
```

## Configuration Options

### CLI Arguments (Override .env)

| Argument | Description | Example |
|----------|-------------|--------|
| `--mode`, `-m` | backtest or live | `--mode live` |
| `--source`, `-s` | free or api | `--source free` |
| `--strategy` | Strategy name | `--strategy sma_crossover` |
| `--fast` | Fast SMA period | `--fast 10` |
| `--slow` | Slow SMA period | `--slow 30` |
| `--symbol` | Trading symbol | `--symbol BANKNIFTY` |
| `--qty` | Quantity per trade | `--qty 50` |
| `--balance` | Initial balance | `--balance 500000` |
| `--stop-loss` | Stop-loss % | `--stop-loss 0.03` |
| `--take-profit` | Take-profit % | `--take-profit 0.05` |
| `--days` | History days | `--days 60` |
| `--interval` | Candle interval | `--interval 15m` |
| `--refresh`, `-r` | Force data refresh | `--refresh` |
| `--list-strategies` | List strategies | |
| `--list-sources` | List data sources | |

### `.env` file (Defaults):
- `MODE`: `BACKTEST` or `LIVE`
- `DATA_SOURCE`: `API` (Kite) or `FREE` (Yahoo Finance)
- `STRATEGY_NAME`: Strategy to use (default: sma_crossover)
- `STRATEGY_FAST_PERIOD`: Fast SMA period (default: 5)
- `STRATEGY_SLOW_PERIOD`: Slow SMA period (default: 20)
- `INITIAL_BALANCE`: Starting capital (default: 2,000,000)
- `QTY`: Shares per trade (default: 25)
- `STOP_LOSS_PERCENT`: Stop-loss threshold (default: 0.02 = 2%)
- `TAKE_PROFIT_PERCENT`: Take-profit threshold (default: 0.04 = 4%)
- `LIVE_INTERVAL_SECONDS`: Time between iterations in live mode (default: 300 = 5min)
- `FORCE_DATA_REFRESH`: Set to `true` to always download fresh data (default: false)
- `DATA_HISTORY_DAYS`: Days of historical data to fetch (default: 30)
- `DATA_INTERVAL`: Candle interval - `1m`, `5m`, `15m`, `1h`, `1d` (default: 5m)

### Priority Order
1. **CLI arguments** (highest)
2. **.env file**
3. **Built-in defaults** (lowest)

## Auto Data Fetching (Smart Cache)

The bot automatically fetches real NIFTY data from Yahoo Finance when running backtests.

### How It Works:

```
Run main.py (BACKTEST mode)
       │
       ▼
┌─────────────────────────┐
│ Check data_metadata.json│
│ - Last fetch time?      │
│ - Data file exists?     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐     YES     ┌──────────────────┐
│ Data stale (>1hr old)?  │────────────▶│ Download fresh   │
│ OR file missing?        │             │ data from Yahoo  │
│ OR force refresh?       │             │ Finance (FREE)   │
└───────────┬─────────────┘             └────────┬─────────┘
            │ NO                                 │
            ▼                                    ▼
┌─────────────────────────┐             ┌──────────────────┐
│ Use cached data from    │             │ Save to CSV +    │
│ historical_prices.csv   │             │ Update metadata  │
└───────────┬─────────────┘             └────────┬─────────┘
            │                                    │
            └──────────────┬─────────────────────┘
                           ▼
                    Run Backtest
```

### Data Refresh Rules:

| Condition | Action |
|-----------|--------|
| No data file exists | Download fresh data |
| Data older than 1 hour | Download fresh data |
| `FORCE_DATA_REFRESH=true` | Always download fresh data |
| Market hours (9:15 AM - 3:30 PM IST) | Refresh if data > 6 min old |
| Data is fresh | Use cached data (fast!) |

### Metadata Tracking:

The file `src/data_metadata.json` tracks:
```json
{
  "last_fetch_time": "2025-12-25T15:19:52",
  "symbol": "NIFTY",
  "interval": "5m",
  "candle_count": 1576,
  "data_start": "2025-11-25 15:15:00+05:30",
  "data_end": "2025-12-24 15:25:00+05:30",
  "price_min": 25712.25,
  "price_max": 26311.00
}
```

### Example Output:

**First run (downloads data):**
```
DATA FRESHNESS CHECK
==================================================
No previous fetch recorded
Refreshing data: No historical data file found
Downloading 30 days of 5m data for ^NSEI...
Downloaded 1576 candles
Data refresh complete!
```

**Second run (uses cache):**
```
DATA FRESHNESS CHECK
==================================================
Last fetch: 2025-12-25T15:19:52
Symbol: NIFTY
Candles: 1576
Using cached data: Data is fresh (fetched 0.0 hours ago)
```

### Force Fresh Data:

To always download fresh data, edit `.env`:
```env
FORCE_DATA_REFRESH=true
```

Or manually delete the cache:
```bash
del historical_prices.csv
del src\data_metadata.json
```

## Viewing Results

### Trade Logs:
- **Backtest**: `src/logs/backtest_trades_log.csv`
- **Live**: `src/logs/trades_log.csv`

### Bot Logs:
- `src/logs/kite_bot.log` - All INFO, WARNING, and ERROR messages

## Understanding the Strategy

**SMA Crossover Strategy**:
- **Fast SMA**: 5-period moving average
- **Slow SMA**: 20-period moving average
- **BUY Signal**: Fast SMA crosses above Slow SMA
- **SELL Signal**: Fast SMA crosses below Slow SMA

**Risk Management**:
- Stop-loss automatically sells if price drops 2% below entry
- Take-profit automatically sells if price rises 4% above entry

## Project Structure

```
kite-paper-trading-bot/
├── src/
│   ├── main.py              # Entry point & CLI parsing
│   ├── core/                # Core engine modules
│   │   ├── backtester.py    # Backtesting engine
│   │   └── registry.py      # Strategy & DataSource factories
│   ├── broker/
│   │   ├── paper.py         # Paper trading broker (no real money)
│   │   └── kite.py          # Kite API wrapper
│   ├── data/
│   │   ├── base.py          # BaseDataSource ABC
│   │   ├── kite.py          # Kite Connect data source
│   │   ├── yahoo.py         # Yahoo Finance data source (free)
│   │   ├── data_manager.py  # Smart data caching & auto-fetch
│   │   ├── download_data.py # Manual data download script
│   │   ├── data_metadata.json   # Cache metadata
│   │   └── historical_prices.csv# Cached price data
│   ├── strategy/
│   │   ├── base.py          # BaseStrategy ABC
│   │   └── sma_crossover.py # SMA crossover strategy
│   └── utils/
│       └── logger.py        # Logging configuration
├── logs/                    # Trade and bot logs
│   ├── backtest_trades_log.csv
│   ├── kite_bot.log
│   └── trades_log.csv
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md
│   ├── QUICKSTART.md
│   └── strategies.txt
├── .env                     # Configuration
├── requirements.txt         # Python dependencies
└── README.md                # Project overview
```

## Safety Notes

- This bot uses **paper trading only** - no real money is at risk
- The PaperBroker class simulates all trades
- All transactions are logged for review
- Stop-loss and take-profit are enforced automatically

## Next Steps

1. **Backtest first**: Always test your strategy on historical data
2. **Monitor in live mode**: Use FREE data source to test live logic
3. **Analyze logs**: Review trade logs to understand performance
4. **Tune parameters**: Adjust SMA periods, stop-loss, take-profit in code
5. **Add strategies**: Create new strategy files in `src/strategy/`

## Troubleshooting

### "No module named 'pandas'"
```bash
cd ..
pip install -r requirements.txt
```

### "No historical data"
Make sure `historical_prices.csv` exists in the project root (not in src/)

### "BUY failed - insufficient balance"
Increase `INITIAL_BALANCE` or decrease `QTY` in `.env`

### Bot won't stop in live mode
Create a file named `stop_bot` in the project root:
```bash
# In project root
New-Item -Path stop_bot -ItemType File
```
