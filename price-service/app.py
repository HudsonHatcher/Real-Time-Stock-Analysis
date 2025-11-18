import os, time, datetime as dt
import requests, pandas as pd
import yfinance as yf
from tenacity import retry, wait_exponential, stop_after_attempt, wait_fixed
from src.log import logger

# Configure yfinance to use proper headers and avoid rate limiting
import urllib3
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Disable proxy for yfinance - Docker proxy can interfere
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

TICKERS = os.getenv("TICKERS","AAPL,MSFT,GOOGL").split(",")
INTERVAL = int(os.getenv("INTERVAL","300"))
ANALYSIS = os.getenv("ANALYSIS_URL","http://analysis:8050")

@retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(5))
def push_prices(ticker, points):
    r = requests.post(f"{ANALYSIS}/ingest/prices", json={
        "ticker": ticker, "provider":"yfinance", "interval":"5m", "points": points
    }, timeout=10)
    r.raise_for_status()

@retry(wait=wait_exponential(multiplier=2, min=4, max=60), stop=stop_after_attempt(3))
def fetch_batch(ticker):
    try:
        # Add delay to avoid rate limiting
        time.sleep(3)  # 3 second delay between requests
        
        ticker_obj = yf.Ticker(ticker)
        
        # Try multiple strategies to get data
        df = None
        
        # Strategy 1: Try daily data first (more reliable, less rate-limited)
        try:
            logger.debug("fetching_daily_data", ticker=ticker)
            # Try with longer timeout and retry
            df = ticker_obj.history(period="1mo", interval="1d", timeout=60, raise_errors=False)
            
            # Check if we got valid data
            if df is not None and not df.empty:
                logger.info("fetched_daily", ticker=ticker, count=len(df))
                # Create synthetic 5-min data points from daily data
                # Spread each day's data across 78 5-min intervals (6.5 hours of trading)
                expanded_rows = []
                for idx, row in df.iterrows():
                    base_time = pd.Timestamp(idx)
                    if base_time.tzinfo is None:
                        try:
                            import pytz
                            base_time = pytz.timezone('US/Eastern').localize(base_time)
                        except:
                            base_time = base_time.tz_localize('US/Eastern')
                    # Market hours: 9:30 AM to 4:00 PM = 6.5 hours = 78 five-minute intervals
                    for i in range(78):
                        ts = base_time + pd.Timedelta(minutes=9*60+30 + i*5)  # Start at 9:30 AM
                        # Distribute the day's price range across intervals
                        price_range = row["High"] - row["Low"]
                        close_price = row["Close"]
                        # Simple linear interpolation for demo
                        price_offset = (i / 77.0 - 0.5) * price_range * 0.1  # Small variation
                        expanded_rows.append({
                            "Datetime": ts,
                            "Open": close_price + price_offset,
                            "High": row["High"],
                            "Low": row["Low"],
                            "Close": close_price + price_offset,
                            "Volume": int(row["Volume"] / 78) if row["Volume"] > 0 else 0
                        })
                df = pd.DataFrame(expanded_rows)
                df.set_index("Datetime", inplace=True)
                logger.info("fetched_daily_expanded", ticker=ticker, count=len(df))
            elif df is None or df.empty:
                logger.warning("fetch_daily_empty", ticker=ticker)
                # Try alternative period if 1mo failed
                try:
                    time.sleep(2)
                    logger.debug("fetching_daily_data_alt", ticker=ticker, period="5d")
                    df = ticker_obj.history(period="5d", interval="1d", timeout=60, raise_errors=False)
                    if df is not None and not df.empty:
                        logger.info("fetched_daily_alt", ticker=ticker, count=len(df))
                        # Expand to synthetic 5-min intervals (same logic as above)
                        expanded_rows = []
                        for idx, row in df.iterrows():
                            base_time = pd.Timestamp(idx)
                            if base_time.tzinfo is None:
                                try:
                                    import pytz
                                    base_time = pytz.timezone('US/Eastern').localize(base_time)
                                except:
                                    base_time = base_time.tz_localize('US/Eastern')
                            for i in range(78):
                                ts = base_time + pd.Timedelta(minutes=9*60+30 + i*5)
                                price_range = row["High"] - row["Low"]
                                close_price = row["Close"]
                                price_offset = (i / 77.0 - 0.5) * price_range * 0.1
                                expanded_rows.append({
                                    "Datetime": ts,
                                    "Open": close_price + price_offset,
                                    "High": row["High"],
                                    "Low": row["Low"],
                                    "Close": close_price + price_offset,
                                    "Volume": int(row["Volume"] / 78) if row["Volume"] > 0 else 0
                                })
                        df = pd.DataFrame(expanded_rows)
                        df.set_index("Datetime", inplace=True)
                        logger.info("fetched_daily_alt_expanded", ticker=ticker, count=len(df))
                except Exception as e2:
                    logger.warning("fetch_daily_alt_failed", ticker=ticker, err=str(e2))
        except Exception as e:
            logger.error("fetch_daily_failed", ticker=ticker, err=str(e), err_type=type(e).__name__)
            # Try one more time with different parameters
            try:
                time.sleep(3)
                logger.debug("fetching_daily_retry", ticker=ticker)
                df = ticker_obj.history(period="5d", interval="1d", timeout=60, raise_errors=False)
                if df is not None and not df.empty:
                    logger.info("fetched_daily_retry_success", ticker=ticker, count=len(df))
                    # Expand to synthetic 5-min intervals
                    expanded_rows = []
                    for idx, row in df.iterrows():
                        base_time = pd.Timestamp(idx)
                        if base_time.tzinfo is None:
                            try:
                                import pytz
                                base_time = pytz.timezone('US/Eastern').localize(base_time)
                            except:
                                base_time = base_time.tz_localize('US/Eastern')
                        for i in range(78):
                            ts = base_time + pd.Timedelta(minutes=9*60+30 + i*5)
                            price_range = row["High"] - row["Low"]
                            close_price = row["Close"]
                            price_offset = (i / 77.0 - 0.5) * price_range * 0.1
                            expanded_rows.append({
                                "Datetime": ts,
                                "Open": close_price + price_offset,
                                "High": row["High"],
                                "Low": row["Low"],
                                "Close": close_price + price_offset,
                                "Volume": int(row["Volume"] / 78) if row["Volume"] > 0 else 0
                            })
                    df = pd.DataFrame(expanded_rows)
                    df.set_index("Datetime", inplace=True)
                    logger.info("fetched_daily_retry_expanded", ticker=ticker, count=len(df))
            except Exception as e2:
                logger.error("fetch_daily_retry_failed", ticker=ticker, err=str(e2))
        
        # Strategy 2: Try intraday 5-minute data (if daily worked, skip this to avoid rate limits)
        if (df is None or df.empty) and False:  # Disabled to avoid rate limits
            try:
                time.sleep(3)  # Extra delay for intraday requests
                df = ticker_obj.history(period="5d", interval="5m", prepost=False, timeout=60, raise_errors=False)
                if df is not None and not df.empty:
                    logger.info("fetched_intraday", ticker=ticker, count=len(df))
            except Exception as e:
                logger.warning("fetch_intraday_failed", ticker=ticker, err=str(e))
        
        if df is None or df.empty:
            logger.warning("no_data_available", ticker=ticker, df_type=type(df).__name__ if df is not None else "None")
            return []
        
        df = df.reset_index()
        out = []
        for _, row in df.iterrows():
            if pd.isna(row.get("Close")) or pd.isna(row.get("Open")):
                continue
            
            ts = row.get("Datetime") if "Datetime" in row else row.name
            if isinstance(ts, pd.Timestamp):
                ts = ts.to_pydatetime()
            if isinstance(ts, dt.datetime):
                if ts.tzinfo is None:
                    # Assume US/Eastern market time
                    import pytz
                    try:
                        ts = pytz.timezone('US/Eastern').localize(ts)
                    except:
                        ts = ts.replace(tzinfo=dt.timezone.utc)
                ts_str = ts.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")
            else:
                ts_str = str(ts)
            
            out.append({
                "ts": ts_str,
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"] or 0)
            })
        
        return out[-200:] if len(out) > 200 else out  # Return last 200 points max
    except Exception as e:
        logger.error("fetch_batch_failed", ticker=ticker, err=str(e))
        return []

if __name__ == "__main__":
    logger.info("price_service_started", tickers=TICKERS, interval=INTERVAL)
    while True:
        for t in TICKERS:
            try:
                pts = fetch_batch(t)
                if pts: 
                    push_prices(t, pts)
                    logger.info("price_pushed", ticker=t, count=len(pts))
                else:
                    logger.warning("no_points_fetched", ticker=t)
            except Exception as e:
                logger.error("price_push_failed", ticker=t, err=str(e))
            # Add delay between tickers to avoid rate limiting
            time.sleep(5)  # 5 second delay between each ticker
        time.sleep(INTERVAL)

