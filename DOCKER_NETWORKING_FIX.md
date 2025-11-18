# Docker Networking & Yahoo Finance API Issues

## Problem Identified

Your Docker setup has a **proxy configured** (`http.docker.internal:3128`) that can interfere with external API calls, especially to Yahoo Finance.

## Root Causes

1. **Docker Proxy Configuration**: Docker Desktop is configured to use a proxy at `http.docker.internal:3128`
2. **Yahoo Finance Rate Limiting**: Even with proxy disabled, Yahoo Finance returns HTTP 429 (Too Many Requests) when requests are too frequent
3. **yfinance Library**: The library may not properly handle proxy settings or rate limits

## Fixes Applied

### 1. Disabled Proxy for Price & Fundamentals Services

**In `docker-compose.yml`:**
```yaml
price:
  environment:
    NO_PROXY: "*"
    no_proxy: "*"
```

**In Python code (`price-service/app.py` and `fundementals-service/app.py`):**
```python
# Disable proxy for yfinance - Docker proxy can interfere
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
```

### 2. Added Rate Limiting Protection

- 2-second delay before each request
- 5-second delay between tickers
- Exponential backoff retry logic
- Switched to daily data (less rate-limited than intraday)

## How to Check Your Docker Proxy Settings

```bash
# Check Docker proxy configuration
docker info | grep -i proxy

# Check if containers have proxy env vars
docker compose exec price env | grep -i proxy

# Test network connectivity
docker compose exec price python -c "import requests; r = requests.get('https://www.google.com'); print(r.status_code)"
```

## Additional Docker Settings That Could Block APIs

### 1. Docker Desktop Proxy Settings
- **Location**: Docker Desktop → Settings → Resources → Proxies
- **Fix**: Disable proxy or add exceptions for `*.yahoo.com`, `*.finance.yahoo.com`

### 2. Network Mode
- **Check**: `docker-compose.yml` - ensure services use `bridge` network (default)
- **Fix**: Don't use `network_mode: host` unless necessary

### 3. DNS Settings
- **Check**: Containers should use Docker's DNS (172.x.x.x)
- **Fix**: Add custom DNS if needed:
```yaml
services:
  price:
    dns:
      - 8.8.8.8
      - 8.8.4.4
```

### 4. Firewall/Security Software
- **Check**: macOS Firewall, antivirus, VPN
- **Fix**: Add Docker to firewall exceptions

## Testing Network Connectivity

```bash
# Test DNS resolution
docker compose exec price python -c "import socket; print(socket.gethostbyname('query1.finance.yahoo.com'))"

# Test HTTPS connection
docker compose exec price python -c "import socket; s = socket.socket(); s.settimeout(5); result = s.connect_ex(('query1.finance.yahoo.com', 443)); print('Connection:', 'OK' if result == 0 else 'FAILED'); s.close()"

# Test direct API call
docker compose exec price python -c "import requests; r = requests.get('https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&range=1mo', headers={'User-Agent': 'Mozilla/5.0'}, timeout=10); print(f'Status: {r.status_code}, Length: {len(r.content)}')"
```

## For Your Other Project

If you're experiencing similar issues in another project:

1. **Check Docker proxy settings**: `docker info | grep -i proxy`
2. **Disable proxy in docker-compose.yml**: Add `NO_PROXY: "*"` to service environment
3. **Remove proxy env vars in code**: Use `os.environ.pop()` to remove proxy settings
4. **Check rate limiting**: Look for HTTP 429 errors in logs
5. **Add delays**: Implement delays between API calls
6. **Use alternative data sources**: Consider APIs with better rate limits

## Current Status

- ✅ Proxy disabled for price and fundamentals services
- ✅ Rate limiting delays implemented
- ⚠️ Yahoo Finance still rate-limiting (may need to wait 15-30 minutes or use alternative API)

## Alternative Solutions

If Yahoo Finance continues to block:

1. **Use Alpha Vantage** (free tier: 5 calls/min, 500 calls/day)
2. **Use Finnhub** (free tier: 60 calls/min)
3. **Use Polygon.io** (free tier available)
4. **Implement request caching** to reduce API calls
5. **Use mock data** for development/testing


