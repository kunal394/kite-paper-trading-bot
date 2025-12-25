"""
Download FREE historical OHLC data from Yahoo Finance
No API key required!
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def download_nifty_data(symbol="^NSEI", days=60, interval="5m"):
    """
    Download historical data from Yahoo Finance.
    
    Parameters:
    - symbol: Yahoo Finance symbol (^NSEI for NIFTY 50, ^NSEBANK for Bank NIFTY)
    - days: Number of days of history (max 60 days for 5m interval)
    - interval: Candle interval (1m, 5m, 15m, 1h, 1d)
    
    Yahoo Finance Symbols:
    - ^NSEI = NIFTY 50
    - ^NSEBANK = Bank NIFTY
    - RELIANCE.NS = Reliance Industries
    - TCS.NS = TCS
    - INFY.NS = Infosys
    """
    print(f"Downloading {days} days of {interval} data for {symbol}...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Download data
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start_date, end=end_date, interval=interval)
    
    if df.empty:
        print("No data received. Try a different symbol or shorter period.")
        return None
    
    # Rename columns to match our format
    df = df.reset_index()
    df.columns = df.columns.str.lower()
    
    # Handle datetime column name (can be 'date' or 'datetime')
    if 'datetime' in df.columns:
        df = df.rename(columns={'datetime': 'timestamp'})
    elif 'date' in df.columns:
        df = df.rename(columns={'date': 'timestamp'})
    
    # Keep only required columns
    df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
    
    print(f"Downloaded {len(df)} candles")
    print(f"Date range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
    print(f"Price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    return df


def save_for_backtest(df, filename="../historical_prices.csv"):
    """Save data in format compatible with backtester"""
    # Keep only required columns
    df_save = df[['timestamp', 'open', 'high', 'low', 'close']].copy()
    df_save.to_csv(filename, index=False)
    print(f"Saved to {filename}")


if __name__ == "__main__":
    # Download NIFTY 50 data
    print("=" * 50)
    print("Downloading REAL NIFTY 50 Historical Data")
    print("=" * 50)
    
    # For 5-minute data, Yahoo allows max ~60 days
    # For daily data, you can go back years
    
    # Option 1: 5-minute candles (last 60 days)
    df = download_nifty_data(symbol="^NSEI", days=30, interval="5m")
    
    # Option 2: Daily candles (last 2 years) - uncomment to use
    # df = download_nifty_data(symbol="^NSEI", days=730, interval="1d")
    
    if df is not None:
        # Save for backtesting
        save_for_backtest(df)
        
        # Show sample
        print("\nSample data:")
        print(df.tail(10))
        
        print("\n" + "=" * 50)
        print("SUCCESS! Real NIFTY data saved to historical_prices.csv")
        print("Now run: cd src && python main.py")
        print("=" * 50)
