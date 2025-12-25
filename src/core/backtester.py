"""
Backtester Module

Runs trading strategies against historical data to evaluate performance.
"""
import sys
import os
import pandas as pd
from typing import Union, Optional
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from broker.paper import PaperBroker
from strategy.base import BaseStrategy
from strategy.sma_crossover import SMACrossoverStrategy
from utils.logger import logger

# Load environment variables
load_dotenv()

# Optional defaults from env
DEFAULT_INITIAL_BALANCE = float(os.getenv("INITIAL_BALANCE", 1000000))
DEFAULT_STOP_LOSS = float(os.getenv("STOP_LOSS_PERCENT", 0.02))
DEFAULT_TAKE_PROFIT = float(os.getenv("TAKE_PROFIT_PERCENT", 0.04))

# CSV log file for backtesting trades - use project root logs folder
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Get trades CSV path from env or use default, ensure it's relative to project root
_trades_csv_env = os.getenv("BACKTEST_TRADES_CSV")
if _trades_csv_env and not os.path.isabs(_trades_csv_env):
    TRADES_CSV = os.path.join(PROJECT_ROOT, _trades_csv_env)
else:
    TRADES_CSV = _trades_csv_env or os.path.join(LOGS_DIR, "backtest_trades_log.csv")

if not os.path.exists(TRADES_CSV):
    pd.DataFrame(columns=["timestamp", "symbol", "action", "price", "qty", "pnl"]).to_csv(TRADES_CSV, index=False)


def log_trade_csv(action, symbol, price, qty, pnl=0):
    """Log trade to CSV file"""
    df_log = pd.DataFrame([{
        "timestamp": datetime.now(),
        "symbol": symbol,
        "action": action,
        "price": price,
        "qty": qty,
        "pnl": pnl
    }])
    df_log.to_csv(TRADES_CSV, mode='a', header=False, index=False)


def backtest(
    df: pd.DataFrame,
    strategy: Optional[BaseStrategy] = None,
    initial_balance: float = DEFAULT_INITIAL_BALANCE,
    symbol: str = "NIFTY",
    qty: int = 50,
    stop_loss_percent: float = DEFAULT_STOP_LOSS,
    take_profit_percent: float = DEFAULT_TAKE_PROFIT
) -> PaperBroker:
    """
    Backtest a trading strategy on historical OHLC data.
    
    Parameters:
        df: DataFrame with OHLC data (must have 'close' column)
        strategy: Strategy instance (defaults to SMACrossoverStrategy)
        initial_balance: Starting balance for paper trading
        symbol: Trading symbol for position tracking
        qty: Quantity to trade per signal
        stop_loss_percent: Stop-loss threshold (e.g., 0.02 = 2%)
        take_profit_percent: Take-profit threshold (e.g., 0.04 = 4%)
    
    Returns:
        PaperBroker instance with final balance and positions
    """
    # Default to SMA Crossover if no strategy provided
    if strategy is None:
        strategy = SMACrossoverStrategy(fast_period=5, slow_period=20)
        logger.info(f"Using default strategy: {strategy.name}")
    
    # Get minimum periods required by the strategy
    min_periods = strategy.get_required_periods()
    logger.info(f"Strategy: {strategy.name} | Required periods: {min_periods}")
    
    broker = PaperBroker(initial_balance)

    for i in range(min_periods, len(df)):
        window_df = df.iloc[:i+1]
        signal = strategy.generate_signal(window_df)
        price = window_df["close"].iloc[-1]
        
        # Log the signal for debugging
        if signal != "HOLD":
            logger.info(f"Row {i}: Signal={signal}, Price={price}")

        # Stop-loss / take-profit check
        for pos_symbol, pos in list(broker.positions.items()):
            pos_price = pos["avg_price"]
            if price <= pos_price * (1 - stop_loss_percent):
                pnl = broker.sell(pos_symbol, price)
                logger.warning(f"Backtest STOP-LOSS: SELL {pos_symbol} at {price} | PnL: {pnl}")
                log_trade_csv("STOP-LOSS", pos_symbol, price, pos["qty"], pnl)
            elif price >= pos_price * (1 + take_profit_percent):
                pnl = broker.sell(pos_symbol, price)
                logger.info(f"Backtest TAKE-PROFIT: SELL {pos_symbol} at {price} | PnL: {pnl}")
                log_trade_csv("TAKE-PROFIT", pos_symbol, price, pos["qty"], pnl)

        # Execute trade based on signal
        if signal == "BUY":
            success = broker.buy(symbol, price, qty)
            if success:
                logger.info(f"Backtest BUY {qty} {symbol} at {price}")
                log_trade_csv("BUY", symbol, price, qty)
            else:
                logger.warning(f"Backtest BUY failed - insufficient balance")
        elif signal == "SELL":
            pnl = broker.sell(symbol, price)
            if pnl:
                logger.info(f"Backtest SELL {symbol} at {price} | PnL: {pnl}")
                log_trade_csv("SELL", symbol, price, qty, pnl)
            else:
                logger.warning(f"Backtest SELL failed - no position to sell")

    # Log final results
    logger.info(f"Backtest complete | Final Balance: {broker.balance:.2f}")
    logger.info(f"Open Positions: {broker.positions}")
    
    # Log strategy statistics if available
    history = strategy.get_signal_history()
    buy_count = sum(1 for s in history if s == "BUY")
    sell_count = sum(1 for s in history if s == "SELL")
    hold_count = sum(1 for s in history if s == "HOLD")
    logger.info(f"Strategy Stats: BUY={buy_count}, SELL={sell_count}, HOLD={hold_count}")
    
    return broker
