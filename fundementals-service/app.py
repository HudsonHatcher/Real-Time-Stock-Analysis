import os, time, datetime as dt
import requests, yfinance as yf
from tenacity import retry, wait_exponential, stop_after_attempt
from src.log import logger

# Disable proxy for yfinance - Docker proxy can interfere
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

TICKERS = os.getenv("TICKERS","AAPL,MSFT,GOOGL").split(",")
REFRESH = int(os.getenv("REFRESH_SECONDS","3600"))
ANALYSIS = os.getenv("ANALYSIS_URL","http://analysis:8050")

def _get_attr_or_dict(info, *keys):
    """Try to get attribute from info object, fallback to dict access"""
    for key in keys:
        # Try attribute access first
        try:
            val = getattr(info, key, None)
            if val is not None:
                return val
        except:
            pass
        # Try dict-style access (for dict-like objects)
        try:
            if isinstance(info, dict):
                val = info.get(key, None)
                if val is not None:
                    return val
            elif hasattr(info, 'get'):
                val = info.get(key, None)
                if val is not None:
                    return val
            elif hasattr(info, '__getitem__'):
                val = info[key] if key in info else None
                if val is not None:
                    return val
        except (KeyError, TypeError, AttributeError):
            pass
    return None

def get_metrics(t):
    try:
        # Add delay to avoid rate limiting
        time.sleep(1)
        
        ticker = yf.Ticker(t)
        
        # Try fast_info first (faster, less data)
        info = None
        try:
            info = ticker.fast_info
            # Check if fast_info actually has data by trying to access a common attribute
            _ = info.get('currency', None) if hasattr(info, 'get') else getattr(info, 'currency', None)
        except Exception as e:
            logger.warning("fast_info_failed", ticker=t, err=str(e))
            # Fallback to full info dict if fast_info fails
            try:
                info = ticker.info
            except Exception as e2:
                logger.error("info_fetch_failed", ticker=t, err=str(e2))
                raise
        
        # Try multiple attribute name variations
        pe = _get_attr_or_dict(info, "trailingPE", "trailingPe", "pe_ratio", "peRatio", "trailingP/E", "forwardPE")
        mc = _get_attr_or_dict(info, "marketCap", "market_cap", "market_capitalization")
        lo = _get_attr_or_dict(info, "fiftyTwoWeekLow", "fifty_two_week_low", "52WeekLow", "yearLow", "year_low")
        hi = _get_attr_or_dict(info, "fiftyTwoWeekHigh", "fifty_two_week_high", "52WeekHigh", "yearHigh", "year_high")
        
        # Convert to floats if not None
        result = {
          "pe_ttm": float(pe) if pe is not None else None,
          "market_cap": float(mc) if mc is not None else None,
          "fifty_two_week_high": float(hi) if hi is not None else None,
          "fifty_two_week_low": float(lo) if lo is not None else None
        }
        
        # Log what we got for debugging
        logger.debug("metrics_fetched", ticker=t, metrics=result)
        
        return result
    except Exception as e:
        logger.error("metrics_fetch_failed", ticker=t, err=str(e), err_type=type(e).__name__)
        return {
          "pe_ttm": None,
          "market_cap": None,
          "fifty_two_week_high": None,
          "fifty_two_week_low": None
        }

@retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(5))
def push_fundamentals(ticker, metrics):
    r = requests.post(f"{ANALYSIS}/ingest/fundamentals", json={
      "ticker": ticker, "provider": "yfinance",
      "as_of": dt.date.today().isoformat(),
      "metrics": metrics
    }, timeout=10)
    r.raise_for_status()

if __name__ == "__main__":
    logger.info("fundamentals_service_started", tickers=TICKERS, refresh_seconds=REFRESH)
    while True:
        for t in TICKERS:
            try:
                metrics = get_metrics(t)
                push_fundamentals(t, metrics)
                logger.info("fundamentals_pushed", ticker=t, metrics=metrics)
            except Exception as e:
                logger.error("fundamentals_push_failed", ticker=t, err=str(e))
        time.sleep(REFRESH)

