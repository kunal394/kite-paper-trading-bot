"""
Kite Paper Trading Bot - Main Entry Point

This bot supports:
- BACKTEST mode: Test strategies against historical data
- LIVE mode: Run strategies with real-time market data (paper trading)

Data Sources:
- FREE (default): Yahoo Finance (no API key required)
- API: Kite Connect (requires subscription)

Strategies:
- sma_crossover: Simple Moving Average Crossover (default)

Usage:
    python main.py                           # Use .env defaults
    python main.py --mode live               # Override mode
    python main.py --strategy sma_crossover --fast 10 --slow 30
    python main.py --help                    # Show all options
"""
import argparse
import pandas as pd
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# === Load environment variables first (as defaults) ===
load_dotenv()


def parse_args():
    """Parse command-line arguments with .env as defaults"""
    parser = argparse.ArgumentParser(
        description="Kite Paper Trading Bot - Backtest or Live Paper Trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Run with .env defaults
  python main.py --mode backtest                    # Backtest mode
  python main.py --mode live --source free          # Live mode with Yahoo Finance
  python main.py --strategy sma_crossover --fast 10 --slow 30
  python main.py --symbol BANKNIFTY --qty 10
  python main.py --days 60 --refresh                # Fetch 60 days, force refresh
        """
    )
    
    # Mode and core settings
    parser.add_argument(
        "-m", "--mode",
        choices=["backtest", "live"],
        default=os.getenv("MODE", "BACKTEST").lower(),
        help="Trading mode: backtest or live (default: from .env or 'backtest')"
    )
    
    parser.add_argument(
        "-s", "--source",
        choices=["free", "api"],
        default=os.getenv("DATA_SOURCE", "FREE").lower(),
        help="Data source: free (Yahoo Finance) or api (Kite) (default: from .env or 'free')"
    )
    
    # Strategy settings
    parser.add_argument(
        "--strategy",
        default=os.getenv("STRATEGY_NAME", "sma_crossover"),
        help="Strategy name (default: from .env or 'sma_crossover')"
    )
    
    parser.add_argument(
        "--fast",
        type=int,
        default=int(os.getenv("STRATEGY_FAST_PERIOD", 5)),
        help="Fast period for SMA strategy (default: from .env or 5)"
    )
    
    parser.add_argument(
        "--slow",
        type=int,
        default=int(os.getenv("STRATEGY_SLOW_PERIOD", 20)),
        help="Slow period for SMA strategy (default: from .env or 20)"
    )
    
    # Trading settings
    parser.add_argument(
        "--symbol",
        default=os.getenv("SYMBOL", "NIFTY"),
        help="Trading symbol (default: from .env or 'NIFTY')"
    )
    
    parser.add_argument(
        "--qty",
        type=int,
        default=int(os.getenv("QTY", 50)),
        help="Quantity per trade (default: from .env or 50)"
    )
    
    parser.add_argument(
        "--balance",
        type=float,
        default=float(os.getenv("INITIAL_BALANCE", 1000000)),
        help="Initial balance (default: from .env or 1000000)"
    )
    
    # Risk management
    parser.add_argument(
        "--stop-loss",
        type=float,
        default=float(os.getenv("STOP_LOSS_PERCENT", 0.02)),
        help="Stop-loss percentage as decimal (default: from .env or 0.02)"
    )
    
    parser.add_argument(
        "--take-profit",
        type=float,
        default=float(os.getenv("TAKE_PROFIT_PERCENT", 0.04)),
        help="Take-profit percentage as decimal (default: from .env or 0.04)"
    )
    
    # Data settings
    parser.add_argument(
        "--days",
        type=int,
        default=int(os.getenv("DATA_HISTORY_DAYS", 30)),
        help="Days of historical data to fetch (default: from .env or 30)"
    )
    
    parser.add_argument(
        "--interval",
        default=os.getenv("DATA_INTERVAL", "5m"),
        help="Candle interval: 1m, 5m, 15m, 1h, 1d (default: from .env or '5m')"
    )
    
    parser.add_argument(
        "--refresh", "-r",
        action="store_true",
        default=os.getenv("FORCE_DATA_REFRESH", "false").lower() == "true",
        help="Force refresh of historical data"
    )
    
    # Utility
    parser.add_argument(
        "--list-strategies",
        action="store_true",
        help="List available strategies and exit"
    )
    
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="List available data sources and exit"
    )
    
    return parser.parse_args()


# Parse arguments
args = parse_args()

# === Import modules ===
from broker.paper import PaperBroker
from utils.logger import logger
from core.backtester import backtest
from data.data_manager import ensure_fresh_data, print_data_status
from core.registry import get_strategy, get_data_source, initialize_registries, StrategyRegistry, DataSourceRegistry

# Initialize the registries
initialize_registries()

# === Handle utility commands ===
if args.list_strategies:
    print("\nAvailable Strategies:")
    print("-" * 40)
    for name, info in StrategyRegistry.list_all().items():
        print(f"  {name}: {info['description']}")
    print()
    exit(0)

if args.list_sources:
    print("\nAvailable Data Sources:")
    print("-" * 40)
    for name, info in DataSourceRegistry.list_all().items():
        auth = "(requires auth)" if info['requires_auth'] else "(free)"
        print(f"  {name}: {info['description']} {auth}")
    print()
    exit(0)

# === Configuration from args (which already have .env as defaults) ===
MODE = args.mode.upper()
DATA_SOURCE = args.source.upper()
INITIAL_BALANCE = args.balance
SYMBOL = args.symbol
QTY = args.qty
STOP_LOSS_PERCENT = args.stop_loss
TAKE_PROFIT_PERCENT = args.take_profit
STRATEGY_NAME = args.strategy
STRATEGY_FAST_PERIOD = args.fast
STRATEGY_SLOW_PERIOD = args.slow
DATA_HISTORY_DAYS = args.days
DATA_INTERVAL = args.interval
FORCE_DATA_REFRESH = args.refresh

# These still come from .env only (not commonly changed via CLI)
INSTRUMENT_TOKEN = os.getenv("NIFTY_TOKEN", "256265")
INTERVAL_SECONDS = int(os.getenv("LIVE_INTERVAL_SECONDS", 300))
KILL_SWITCH_FILE = os.getenv("KILL_SWITCH_FILE", "stop_bot")
TRADES_CSV = os.getenv("LIVE_TRADES_CSV", "logs/trades_log.csv")

# === Ensure logs folder exists ===
if not os.path.exists(os.path.dirname(TRADES_CSV)):
    os.makedirs(os.path.dirname(TRADES_CSV))

# Initialize CSV if not exists
if not os.path.exists(TRADES_CSV):
    pd.DataFrame(columns=["timestamp", "symbol", "action", "price", "qty", "pnl"]).to_csv(TRADES_CSV, index=False)

# === Create strategy instance ===
try:
    strategy = get_strategy(
        STRATEGY_NAME,
        fast_period=STRATEGY_FAST_PERIOD,
        slow_period=STRATEGY_SLOW_PERIOD
    )
    logger.info(f"Using strategy: {strategy.name} (fast={STRATEGY_FAST_PERIOD}, slow={STRATEGY_SLOW_PERIOD})")
except ValueError as e:
    logger.error(f"Failed to load strategy: {e}")
    exit(1)

# === Import Kite API if needed ===
if DATA_SOURCE == "API":
    from broker.kite import get_kite_client
    from data.market import KiteDataSource

# === Helper: log trade to CSV ===
def log_trade_csv(action, symbol, price, qty, pnl=0):
    df_log = pd.DataFrame([{
        "timestamp": datetime.now(),
        "symbol": symbol,
        "action": action,
        "price": price,
        "qty": qty,
        "pnl": pnl
    }])
    df_log.to_csv(TRADES_CSV, mode='a', header=False, index=False)

# === Initialize Paper Broker ===
broker = PaperBroker(INITIAL_BALANCE)

# === Helper: check stop-loss / take-profit for all positions ===
def check_sl_tp(price):
    for pos_symbol, pos in list(broker.positions.items()):
        avg_price = pos["avg_price"]
        qty = pos["qty"]
        if price <= avg_price * (1 - STOP_LOSS_PERCENT):
            pnl = broker.sell(pos_symbol, price)
            logger.warning(f"STOP-LOSS triggered: SELL {pos_symbol} at {price} | PnL: {pnl}")
            log_trade_csv("STOP-LOSS", pos_symbol, price, qty, pnl)
        elif price >= avg_price * (1 + TAKE_PROFIT_PERCENT):
            pnl = broker.sell(pos_symbol, price)
            logger.info(f"TAKE-PROFIT triggered: SELL {pos_symbol} at {price} | PnL: {pnl}")
            log_trade_csv("TAKE-PROFIT", pos_symbol, price, qty, pnl)

# === MAIN LOGIC ===
if MODE == "BACKTEST":
    logger.info("=" * 50)
    logger.info("Running in BACKTEST mode")
    logger.info(f"Strategy: {strategy.name} | Symbol: {SYMBOL}")
    logger.info("=" * 50)
    
    # === Auto-fetch fresh data ===
    # This will check if data needs updating and download if necessary
    df_prices = ensure_fresh_data(
        symbol=SYMBOL,
        days=DATA_HISTORY_DAYS,
        interval=DATA_INTERVAL,
        force=FORCE_DATA_REFRESH
    )
    
    if df_prices is None or df_prices.empty:
        logger.warning("No historical data available. Exiting backtest.")
    else:
        # Show data status
        print_data_status()
        
        # Run backtest with selected strategy
        backtest(
            df=df_prices,
            strategy=strategy,
            initial_balance=INITIAL_BALANCE,
            symbol=SYMBOL,
            qty=QTY,
            stop_loss_percent=STOP_LOSS_PERCENT,
            take_profit_percent=TAKE_PROFIT_PERCENT
        )

elif MODE == "LIVE":
    logger.info("=" * 50)
    logger.info(f"Running in LIVE mode using {DATA_SOURCE} data source")
    logger.info(f"Strategy: {strategy.name} | Symbol: {SYMBOL}")
    logger.info("=" * 50)

    # === Initialize data source ===
    if DATA_SOURCE == "API":
        kite = get_kite_client()
        data_source = get_data_source("kite", kite=kite)
    else:
        data_source = get_data_source("yahoo")
    
    logger.info(f"Data source: {data_source}")

    while True:
        if os.path.exists(KILL_SWITCH_FILE):
            logger.info("Kill switch detected. Stopping live loop.")
            logger.info(f"Final Balance: {broker.balance}")
            logger.info(f"Open Positions: {broker.positions}")
            break

        logger.info("=== Starting new iteration ===")

        # === Fetch latest data using data source ===
        try:
            df_live = data_source.get_historical_data(
                symbol=SYMBOL if DATA_SOURCE != "API" else INSTRUMENT_TOKEN,
                interval="5minute",
                days=1
            )
        except Exception as e:
            logger.error(f"Failed to fetch live data: {e}")
            time.sleep(INTERVAL_SECONDS)
            continue

        if df_live.empty:
            logger.warning("No live data. Retrying...")
            time.sleep(INTERVAL_SECONDS)
            continue

        # --- Strategy signal ---
        signal = strategy.generate_signal(df_live)
        price = df_live["close"].iloc[-1]

        # --- Check stop-loss / take-profit ---
        check_sl_tp(price)

        # --- Execute trade ---
        if signal == "BUY":
            success = broker.buy(SYMBOL, price, QTY)
            if success:
                logger.info(f"BUY {QTY} {SYMBOL} at {price}")
                log_trade_csv("BUY", SYMBOL, price, QTY)
            else:
                logger.warning(f"BUY {SYMBOL} failed. Insufficient balance.")
        elif signal == "SELL":
            pnl = broker.sell(SYMBOL, price)
            if pnl:
                logger.info(f"SELL {SYMBOL} at {price} | PnL: {pnl}")
                log_trade_csv("SELL", SYMBOL, price, QTY, pnl)
            else:
                logger.warning(f"SELL {SYMBOL} failed. No position to sell.")
        else:
            logger.info("HOLD signal. No action taken.")

        # --- Log status ---
        logger.info(f"Balance: {broker.balance}")
        logger.info(f"Positions: {broker.positions}")
        logger.info("=== Iteration complete ===\n")

        # --- Wait before next iteration ---
        time.sleep(INTERVAL_SECONDS)

else:
    logger.error(f"Invalid MODE: {MODE}. Use BACKTEST or LIVE.")
