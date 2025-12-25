"""
Data Manager - Handles data fetching with smart caching and fallback sources
Tracks last fetch time and only downloads new data when needed

Fallback Order:
1. Yahoo Finance (primary - reliable, supports intraday)
2. NSE via nsepy (fallback - direct NSE, daily data only)
"""
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from utils.logger import logger

# Import data sources
try:
    import yfinance as yf
    YAHOO_AVAILABLE = True
except ImportError:
    YAHOO_AVAILABLE = False
    logger.warning("yfinance not installed")

try:
    from nsepy import get_history
    NSEPY_AVAILABLE = True
except ImportError:
    NSEPY_AVAILABLE = False

try:
    from nsetools import Nse
    NSETOOLS_AVAILABLE = True
except ImportError:
    NSETOOLS_AVAILABLE = False

# Metadata file to track fetch history
METADATA_FILE = "data_metadata.json"
DATA_FILE = "historical_prices.csv"

# Default settings
DEFAULT_SYMBOL = "^NSEI"
DEFAULT_DAYS = 30
DEFAULT_INTERVAL = "5m"

# How often to refresh data (in hours)
# During market hours, you might want this lower
DATA_REFRESH_HOURS = 1


def get_metadata():
    """Load metadata about last data fetch"""
    metadata_path = os.path.join(os.path.dirname(__file__), METADATA_FILE)
    
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read metadata: {e}")
    
    return {
        "last_fetch_time": None,
        "symbol": None,
        "interval": None,
        "candle_count": 0,
        "data_start": None,
        "data_end": None
    }


def save_metadata(metadata):
    """Save metadata about data fetch"""
    metadata_path = os.path.join(os.path.dirname(__file__), METADATA_FILE)
    
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    except Exception as e:
        logger.warning(f"Could not save metadata: {e}")


def should_refresh_data(force=False):
    """
    Determine if we need to fetch new data
    
    Returns:
        tuple: (should_refresh: bool, reason: str)
    """
    if force:
        return True, "Force refresh requested"
    
    data_path = os.path.join(os.path.dirname(__file__), DATA_FILE)
    
    # Check if data file exists
    if not os.path.exists(data_path):
        return True, "No historical data file found"
    
    # Check metadata
    metadata = get_metadata()
    
    if metadata["last_fetch_time"] is None:
        return True, "No previous fetch recorded"
    
    # Parse last fetch time
    try:
        last_fetch = datetime.fromisoformat(metadata["last_fetch_time"])
    except:
        return True, "Invalid last fetch time"
    
    # Check if data is stale
    time_since_fetch = datetime.now() - last_fetch
    hours_since_fetch = time_since_fetch.total_seconds() / 3600
    
    if hours_since_fetch >= DATA_REFRESH_HOURS:
        return True, f"Data is {hours_since_fetch:.1f} hours old (threshold: {DATA_REFRESH_HOURS}h)"
    
    # Check if market might have new data
    # NSE market hours: 9:15 AM - 3:30 PM IST
    now = datetime.now()
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    is_weekday = now.weekday() < 5  # Monday = 0, Friday = 4
    is_market_hours = market_open <= now <= market_close
    
    if is_weekday and is_market_hours and hours_since_fetch >= 0.1:  # 6 minutes
        return True, "Market is open and data may have updated"
    
    return False, f"Data is fresh (fetched {hours_since_fetch:.1f} hours ago)"


def download_data(symbol=DEFAULT_SYMBOL, days=DEFAULT_DAYS, interval=DEFAULT_INTERVAL):
    """
    Download historical data with fallback sources.
    
    Fallback Order:
    1. Yahoo Finance (primary - supports intraday)
    2. NSE via nsepy (fallback - daily data only)
    
    Parameters:
        symbol: Trading symbol (NIFTY, BANKNIFTY, RELIANCE, etc.)
        days: Number of days of history
        interval: Candle interval (5m, 15m, 1h, 1d)
    
    Returns:
        DataFrame with OHLC data or None if all sources failed
    """
    df = None
    source_used = None
    
    # === Try Yahoo Finance first (supports intraday) ===
    if YAHOO_AVAILABLE:
        logger.info("[Source 1/2] Trying Yahoo Finance...")
        df = _download_from_yahoo(symbol, days, interval)
        if df is not None and not df.empty:
            source_used = "Yahoo Finance"
            logger.info("[OK] Successfully fetched data from Yahoo Finance")
        else:
            logger.warning("[FAIL] Yahoo Finance failed, trying fallback...")
    else:
        logger.warning("[FAIL] Yahoo Finance not available (yfinance not installed)")
    
    # === Fallback to NSE via nsepy (daily data only) ===
    if (df is None or df.empty) and NSEPY_AVAILABLE:
        logger.info("[Source 2/2] FALLBACK: Trying NSE via nsepy...")
        
        # nsepy only supports daily data
        if interval not in ["1d", "1day", "day"]:
            logger.warning(f"[WARN] NSE fallback only supports daily data, not {interval}")
            logger.warning(f"[WARN] Will fetch daily data instead of {interval}")
        
        df = _download_from_nse(symbol, days)
        if df is not None and not df.empty:
            source_used = "NSE (nsepy)"
            logger.info("[OK] FALLBACK SUCCESS: Fetched data from NSE")
        else:
            logger.warning("[FAIL] NSE fallback also failed")
    elif df is None or df.empty:
        logger.warning("[FAIL] NSE fallback not available (nsepy not installed)")
    
    # === Log final result ===
    if df is not None and not df.empty:
        logger.info(f"[DATA] Source Used: {source_used}")
        logger.info(f"[DATA] Downloaded {len(df)} candles")
        logger.info(f"[DATA] Date range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
        logger.info(f"[DATA] Price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
    else:
        logger.error("[ERROR] ALL DATA SOURCES FAILED - No data available")
    
    return df


def _download_from_yahoo(symbol, days, interval):
    """Download data from Yahoo Finance"""
    # Map common names to Yahoo symbols
    symbol_map = {
        "NIFTY": "^NSEI",
        "NIFTY50": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "RELIANCE": "RELIANCE.NS",
        "TCS": "TCS.NS",
        "INFY": "INFY.NS",
        "HDFCBANK": "HDFCBANK.NS",
        "ICICIBANK": "ICICIBANK.NS",
        "SBIN": "SBIN.NS",
    }
    
    yahoo_symbol = symbol_map.get(symbol.upper(), symbol)
    
    logger.info(f"  Downloading {days} days of {interval} data for {yahoo_symbol}...")
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        ticker = yf.Ticker(yahoo_symbol)
        df = ticker.history(start=start_date, end=end_date, interval=interval)
        
        if df.empty:
            logger.warning(f"  No data received for {yahoo_symbol}")
            return None
        
        # Format columns
        df = df.reset_index()
        df.columns = df.columns.str.lower()
        
        if 'datetime' in df.columns:
            df = df.rename(columns={'datetime': 'timestamp'})
        elif 'date' in df.columns:
            df = df.rename(columns={'date': 'timestamp'})
        
        # Keep only required columns
        cols_to_keep = ['timestamp', 'open', 'high', 'low', 'close']
        if 'volume' in df.columns:
            cols_to_keep.append('volume')
        df = df[[c for c in cols_to_keep if c in df.columns]]
        
        return df
        
    except Exception as e:
        logger.error(f"  Yahoo Finance error: {e}")
        return None


def _download_from_nse(symbol, days):
    """Download data from NSE via nsepy (daily data only)"""
    # Map common names to NSE symbols
    index_map = {
        "NIFTY": "NIFTY 50",
        "NIFTY50": "NIFTY 50",
        "BANKNIFTY": "NIFTY BANK",
    }
    
    is_index = symbol.upper() in index_map
    nse_symbol = index_map.get(symbol.upper(), symbol.upper())
    
    logger.info(f"  Downloading {days} days of daily data for {nse_symbol} from NSE...")
    
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        if is_index:
            df = get_history(symbol=nse_symbol, start=start_date, end=end_date, index=True)
        else:
            df = get_history(symbol=nse_symbol, start=start_date, end=end_date)
        
        if df.empty:
            logger.warning(f"  No data received for {nse_symbol}")
            return None
        
        # Format the DataFrame
        df = df.reset_index()
        df.columns = df.columns.str.lower()
        
        if 'date' in df.columns:
            df = df.rename(columns={'date': 'timestamp'})
        
        # Keep only required columns
        cols_to_keep = ['timestamp', 'open', 'high', 'low', 'close']
        if 'volume' in df.columns:
            cols_to_keep.append('volume')
        df = df[[c for c in cols_to_keep if c in df.columns]]
        
        return df
        
    except Exception as e:
        logger.error(f"  NSE error: {e}")
        return None


def save_data(df, symbol=DEFAULT_SYMBOL, interval=DEFAULT_INTERVAL, source="Unknown"):
    """Save data to CSV and update metadata"""
    data_path = os.path.join(os.path.dirname(__file__), DATA_FILE)
    
    # Save CSV
    cols_to_save = ['timestamp', 'open', 'high', 'low', 'close']
    if 'volume' in df.columns:
        cols_to_save.append('volume')
    df_save = df[[c for c in cols_to_save if c in df.columns]].copy()
    df_save.to_csv(data_path, index=False)
    
    # Update metadata
    metadata = {
        "last_fetch_time": datetime.now().isoformat(),
        "symbol": symbol,
        "interval": interval,
        "candle_count": len(df),
        "data_start": str(df['timestamp'].iloc[0]),
        "data_end": str(df['timestamp'].iloc[-1]),
        "price_min": float(df['close'].min()),
        "price_max": float(df['close'].max()),
        "source": source
    }
    save_metadata(metadata)
    
    logger.info(f"Saved {len(df)} candles to {data_path}")
    return True


def load_data():
    """Load historical data from CSV"""
    data_path = os.path.join(os.path.dirname(__file__), DATA_FILE)
    
    if not os.path.exists(data_path):
        return None
    
    try:
        df = pd.read_csv(data_path)
        return df
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return None


def ensure_fresh_data(symbol="NIFTY", days=30, interval="5m", force=False):
    """
    Main function to ensure we have fresh data for backtesting.
    
    Uses fallback sources if primary source fails:
    1. Yahoo Finance (primary - supports intraday)
    2. NSE via nsepy (fallback - daily data only)
    
    Parameters:
        symbol: Trading symbol
        days: Days of history to fetch
        interval: Candle interval
        force: Force refresh even if data is fresh
    
    Returns:
        DataFrame with OHLC data
    """
    logger.info("=" * 50)
    logger.info("DATA FRESHNESS CHECK")
    logger.info("=" * 50)
    
    # Show available sources
    logger.info(f"Available sources: Yahoo={YAHOO_AVAILABLE}, NSE={NSEPY_AVAILABLE}")
    
    # Check metadata
    metadata = get_metadata()
    
    if metadata["last_fetch_time"]:
        logger.info(f"Last fetch: {metadata['last_fetch_time']}")
        logger.info(f"Symbol: {metadata.get('symbol', 'Unknown')}")
        logger.info(f"Candles: {metadata.get('candle_count', 0)}")
        logger.info(f"Source: {metadata.get('source', 'Unknown')}")
    else:
        logger.info("No previous fetch recorded")
    
    # Determine if refresh needed
    needs_refresh, reason = should_refresh_data(force=force)
    source_used = "Cache"
    
    if needs_refresh:
        logger.info(f"Refreshing data: {reason}")
        
        # Download new data (with fallback logic)
        df = download_data(symbol=symbol, days=days, interval=interval)
        
        if df is not None and not df.empty:
            # Determine which source was used based on logs
            # The download_data function logs the source
            source_used = "Yahoo Finance" if YAHOO_AVAILABLE else "NSE (nsepy)"
            save_data(df, symbol=symbol, interval=interval, source=source_used)
            logger.info("Data refresh complete!")
        else:
            logger.warning("Failed to download new data, using existing data if available")
            df = load_data()
            source_used = "Cache (fallback after failure)"
    else:
        logger.info(f"Using cached data: {reason}")
        df = load_data()
    
    logger.info("=" * 50)
    
    return df


def print_data_status():
    """Print current data status"""
    metadata = get_metadata()
    
    print("\n" + "=" * 50)
    print("DATA STATUS")
    print("=" * 50)
    
    # Show available sources
    print(f"Available Sources:")
    print(f"  - Yahoo Finance: {'[OK] Available' if YAHOO_AVAILABLE else '[X] Not installed'}")
    print(f"  - NSE (nsepy):   {'[OK] Available' if NSEPY_AVAILABLE else '[X] Not installed'}")
    print(f"  - NSE (nsetools):{'[OK] Available' if NSETOOLS_AVAILABLE else '[X] Not installed'}")
    print()
    
    if metadata["last_fetch_time"]:
        last_fetch = datetime.fromisoformat(metadata["last_fetch_time"])
        time_ago = datetime.now() - last_fetch
        hours_ago = time_ago.total_seconds() / 3600
        
        print(f"Last Fetch:    {metadata['last_fetch_time']}")
        print(f"               ({hours_ago:.1f} hours ago)")
        print(f"Source Used:   {metadata.get('source', 'Unknown')}")
        print(f"Symbol:        {metadata.get('symbol', 'Unknown')}")
        print(f"Interval:      {metadata.get('interval', 'Unknown')}")
        print(f"Candles:       {metadata.get('candle_count', 0)}")
        print(f"Data Range:    {metadata.get('data_start', 'N/A')} to")
        print(f"               {metadata.get('data_end', 'N/A')}")
        print(f"Price Range:   {metadata.get('price_min', 0):.2f} - {metadata.get('price_max', 0):.2f}")
    else:
        print("No data has been fetched yet.")
    
    # Check if refresh needed
    needs_refresh, reason = should_refresh_data()
    print(f"\nRefresh Needed: {'Yes' if needs_refresh else 'No'}")
    print(f"Reason:         {reason}")
    print("=" * 50 + "\n")


def get_available_sources():
    """Return dict of available data sources"""
    return {
        "yahoo": YAHOO_AVAILABLE,
        "nsepy": NSEPY_AVAILABLE,
        "nsetools": NSETOOLS_AVAILABLE
    }


if __name__ == "__main__":
    # Test the data manager
    print_data_status()
    
    # Force refresh to test
    df = ensure_fresh_data(symbol="NIFTY", days=30, interval="5m", force=False)
    
    if df is not None:
        print(f"\nLoaded {len(df)} candles")
        print(df.tail(5))
    
    print_data_status()
