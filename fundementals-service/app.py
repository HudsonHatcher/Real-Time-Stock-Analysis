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

def get_metrics(t):
    try:
        ticker = yf.Ticker(t)
        info = ticker.fast_info  # light, modern attr
        pe = getattr(info, "trailingPE", None) or getattr(info, "pe_ratio", None)
        mc = getattr(info, "market_cap", None)
        lo = getattr(info, "fifty_two_week_low", None) or getattr(info, "year_low", None)
        hi = getattr(info, "fifty_two_week_high", None) or getattr(info, "year_high", None)
        return {
          "pe_ttm": float(pe) if pe is not None else None,
          "market_cap": float(mc) if mc is not None else None,
          "fifty_two_week_high": float(hi) if hi is not None else None,
          "fifty_two_week_low": float(lo) if lo is not None else None
        }
    except Exception as e:
        logger.error("metrics_fetch_failed", ticker=t, err=str(e))
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

