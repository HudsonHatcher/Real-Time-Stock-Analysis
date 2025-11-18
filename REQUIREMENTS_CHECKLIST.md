# Requirements Compliance Checklist

## Functional Requirements

### ✅ FR1: At least three distinct Docker containers
**Status: COMPLIANT**
- **Price Service** (`price-service/`) - Polls 5-minute price data
- **Fundamentals Service** (`fundementals-service/`) - Fetches fundamental metrics
- **Analysis & Visualization Service** (`analysis-service/`) - Data fusion, processing, and dashboard
- **Bonus**: Postgres database container (4 containers total, exceeds minimum)

**Evidence:**
- `docker-compose.yml` defines all services
- Each service has its own Dockerfile and isolated codebase

---

### ✅ FR2: Price Polling Service - 5-minute intervals for ≥3 tickers
**Status: COMPLIANT**
- Fetches 5-minute interval data using `yfinance`
- Default tickers: AAPL, MSFT, GOOGL (3+ tickers)
- Polling interval: 300 seconds (5 minutes)
- Configurable via `TICKERS` environment variable

**Evidence:**
- `price-service/app.py`: Line 8 `INTERVAL = 300` (5 minutes)
- `price-service/app.py`: Line 22 `interval="5m"`
- `price-service/app.py`: Line 7 `TICKERS = os.getenv("TICKERS","AAPL,MSFT,GOOGL")`

---

### ✅ FR3: Fundamental Data Service - Financial metrics
**Status: COMPLIANT**
- Fetches P/E Ratio (TTM)
- Fetches Market Cap
- Fetches 52-week high
- Fetches 52-week low
- Uses Yahoo Finance API

**Evidence:**
- `fundementals-service/app.py`: Lines 18-22 define metrics
- Metrics include: `pe_ttm`, `market_cap`, `fifty_two_week_high`, `fifty_two_week_low`

---

### ✅ FR4: Analysis Service - Data Fusion
**Status: COMPLIANT**
- Consumes data from both Price and Fundamentals services
- Links real-time price data with fundamental data by ticker
- Stores both in shared Postgres database
- Dashboard displays fused data together

**Evidence:**
- `analysis-service/app.py`: `/ingest/prices` and `/ingest/fundamentals` endpoints
- `analysis-service/src/db.py`: Both `Prices` and `Fundamentals` tables linked by `ticker`
- `analysis-service/src/dash_app.py`: Dashboard queries both and displays together

---

### ✅ FR5: Technical Indicator Calculation
**Status: COMPLIANT**
- Calculates 20-period Simple Moving Average (SMA20)
- Calculated on-the-fly when data is requested
- Displayed on dashboard chart

**Evidence:**
- `analysis-service/src/indicators.py`: `sma()` function with period parameter
- `analysis-service/app.py`: Line 60 `payload_sma20 = sma(closes, 20)`
- `analysis-service/src/dash_app.py`: SMA20 trace added to chart

---

### ✅ FR6: Unified Dashboard - One Screen
**Status: COMPLIANT**
- User can select stock ticker via dropdown
- Displays time-series price chart
- Displays calculated SMA20 indicator (overlaid on chart)
- Displays fundamental metrics (PE, Market Cap, 52-week high/low)
- All on one screen

**Evidence:**
- `analysis-service/src/dash_app.py`: Lines 56-63 define layout
- Chart shows both Close price and SMA20 lines
- Fundamentals displayed below chart in list format

---

## Non-Functional Requirements

### ✅ NFR1: Infrastructure as Code (Docker Compose)
**Status: COMPLIANT**
- Entire stack automated via `docker-compose.yml`
- Single command deployment: `docker compose up --build`
- Startup script (`start.sh`) provides additional automation

**Evidence:**
- `docker-compose.yml`: Defines all services, networks, volumes
- `start.sh`: Automated startup with validation checks
- README.md: Clear deployment instructions

---

### ✅ NFR2: Data Schemas - Defined, Visualized, Explained
**Status: COMPLIANT**

**Defined: ✅**
- Price data schema: `price-service/src/schema.py` (Pydantic models)
- Fundamentals schema: `fundementals-service/src/schema.py` (Pydantic models)
- Database schema: `analysis-service/src/db.py` (SQLAlchemy models)

**Visualized: ✅**
- README includes ASCII diagram of data pipeline flow
- JSON examples showing schema structure
- Database schema documented with table structures

**Explained: ✅**
- Schemas are clearly defined in code with type hints
- README describes data flow and includes schema examples
- Database schema columns and types documented

**Evidence:**
- `README.md`: Lines 64-134 contain complete schema documentation
- Includes JSON examples for both price and fundamentals data
- ASCII diagram showing data pipeline flow

---

### ✅ NFR3: Robust Error Handling
**Status: COMPLIANT**
- API failures handled with retries (tenacity library)
- Exponential backoff: 1s to 60s, max 5 attempts
- Invalid ticker handling: Returns None values, logs error
- Network errors: Caught and logged, service continues
- Structured JSON logging: All errors logged with context

**Evidence:**
- `price-service/app.py`: Lines 11-16, 44-45 (retry decorator, error handling)
- `fundementals-service/app.py`: Lines 24-31, 33-40, 50-51 (error handling)
- `analysis-service/app.py`: Lines 30-31, 51-52 (HTTP exception handling)
- All services use `structlog` for structured logging

---

### ✅ NFR4: Near Real-Time Data (≤15 minutes old)
**Status: COMPLIANT**
- Price polling: Every 5 minutes (300 seconds)
- Dashboard refresh: Every 60 seconds
- Maximum data age: 5 minutes (well under 15-minute requirement)

**Evidence:**
- `price-service/app.py`: Line 8 `INTERVAL = 300` (5 minutes)
- `analysis-service/src/dash_app.py`: Line 59 `interval=60*1000` (60 seconds)
- Data fetched from last 65 minutes, ensuring recent data available

---

### ⚠️ NFR5: Dashboard Load Time (<10 seconds)
**Status: LIKELY COMPLIANT** (needs verification)

**Optimizations Implemented:**
- Limits query to 200 most recent points
- Database indexes on (ticker, ts) for fast queries
- Lightweight API responses
- Efficient SMA calculation

**Evidence:**
- `analysis-service/app.py`: Line 55 `window: int = 200`
- `analysis-service/src/db.py`: Primary key on (ticker, ts) provides indexing
- Dashboard uses efficient Plotly rendering

**Note:** Actual load time should be measured, but implementation follows best practices for performance

---

### ✅ NFR6: Clear Container Communication
**Status: COMPLIANT**
- Communication method: REST API calls + Shared Postgres database
- Price Service → Analysis Service: `POST http://analysis:8050/ingest/prices`
- Fundamentals Service → Analysis Service: `POST http://analysis:8050/ingest/fundamentals`
- Analysis Service → Database: SQLAlchemy ORM to Postgres
- Dashboard → Analysis Service: REST API (`GET /api/series/{ticker}`, `GET /api/fundamentals/{ticker}`)

**Evidence:**
- `docker-compose.yml`: Service names used for inter-container communication
- `price-service/app.py`: Line 9 `ANALYSIS_URL: http://analysis:8050`
- `fundementals-service/app.py`: Line 8 `ANALYSIS_URL: http://analysis:8050`
- `analysis-service/app.py`: REST endpoints clearly defined
- README.md: Documents API endpoints and data flow

---

## Summary

| Requirement | Status | Notes |
|------------|--------|-------|
| FR1: 3+ Containers | ✅ COMPLIANT | 4 containers (exceeds requirement) |
| FR2: Price Polling | ✅ COMPLIANT | 5-min intervals, 3+ tickers |
| FR3: Fundamentals | ✅ COMPLIANT | PE, Market Cap, 52w high/low |
| FR4: Data Fusion | ✅ COMPLIANT | Linked by ticker in Postgres |
| FR5: Technical Indicator | ✅ COMPLIANT | SMA20 calculated |
| FR6: Unified Dashboard | ✅ COMPLIANT | All on one screen |
| NFR1: Docker Compose | ✅ COMPLIANT | Full IaC automation |
| NFR2: Schema Docs | ✅ COMPLIANT | Defined, visualized, and explained |
| NFR3: Error Handling | ✅ COMPLIANT | Retries, logging, graceful degradation |
| NFR4: Near Real-Time | ✅ COMPLIANT | 5-min polling (<15 min requirement) |
| NFR5: Load Time | ⚠️ LIKELY | Optimized, needs measurement |
| NFR6: Communication | ✅ COMPLIANT | REST + Shared DB clearly defined |

**Overall Compliance: 11/12 Fully Compliant, 1/12 Needs Verification**

---

## Recommendations for Full Compliance

1. **Performance Testing**: Measure actual dashboard load time and optimize if needed (currently optimized but not measured)

