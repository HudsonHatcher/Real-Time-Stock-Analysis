# Real-Time Stock Analysis Pipeline

A real-time stock analysis system that combines price data and fundamentals into a unified dashboard. Built with Docker Compose, FastAPI, and Plotly Dash.

## Architecture

The system consists of 4 services:
- **Price Service**: Polls 5-minute candles from Yahoo Finance and sends to analysis service
- **Fundamentals Service**: Fetches PE ratio, market cap, and 52-week high/low, sends to analysis service
- **Analysis Service**: FastAPI backend with Plotly Dash dashboard, stores data in Postgres
- **Postgres Database**: Stores price time-series and fundamentals data

## Quick Start

### Option 1: Using the Startup Script (Recommended)

Simply run the startup script which will check all prerequisites and start the services:

```bash
./start.sh
```

The script will:
- ✅ Check Docker and Docker Compose installation
- ✅ Verify all required files are present
- ✅ Create `.env` file if it doesn't exist
- ✅ Check port availability
- ✅ Build and start all containers

### Option 2: Manual Setup

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env to set your tickers (default: AAPL,MSFT,GOOGL)
   ```

2. **Build and run:**
   ```bash
   docker compose up --build
   ```

3. **Open the dashboard:**
   ```
   http://localhost:8050
   ```

## Features

- Real-time 5-minute price candles
- Technical indicators (SMA20)
- Fundamental metrics (PE, Market Cap, 52-week high/low)
- Unified dashboard showing price chart with indicators and fundamentals
- Automatic retries with exponential backoff
- Structured JSON logging

## Data Flow

1. Price service polls Yahoo Finance every 5 minutes → POSTs to `/ingest/prices`
2. Fundamentals service fetches metrics hourly → POSTs to `/ingest/fundamentals`
3. Analysis service stores data in Postgres → computes SMA20 on read
4. Dashboard queries API → renders time-series + indicator + fundamentals

## Data Schemas

### Price Data Schema (In Motion)

```json
{
  "ticker": "AAPL",
  "provider": "yfinance",
  "interval": "5m",
  "points": [
    {
      "ts": "2025-11-17T16:35:00Z",
      "open": 223.10,
      "high": 223.40,
      "low": 222.85,
      "close": 223.25,
      "volume": 154320
    }
  ]
}
```

**Database Schema:**
- Table: `prices`
- Primary Key: `(ticker, ts)`
- Columns: `ticker` (String), `ts` (DateTime), `open`, `high`, `low`, `close` (Numeric), `volume` (BigInteger)

### Fundamentals Data Schema (In Motion)

```json
{
  "ticker": "AAPL",
  "provider": "yfinance",
  "as_of": "2025-11-17",
  "metrics": {
    "pe_ttm": 34.2,
    "market_cap": 3470000000000,
    "fifty_two_week_high": 237.00,
    "fifty_two_week_low": 164.31
  }
}
```

**Database Schema:**
- Table: `fundamentals`
- Primary Key: `ticker`
- Columns: `ticker` (String), `as_of` (Date), `pe_ttm`, `market_cap`, `fifty_two_week_high`, `fifty_two_week_low` (Numeric), `updated_at` (DateTime)

### Data Pipeline Flow

```
┌─────────────────┐         ┌──────────────────┐
│  Price Service  │────────▶│  Analysis Service│
│  (5-min polls)  │  REST   │  /ingest/prices  │
└─────────────────┘         └────────┬─────────┘
                                     │
┌─────────────────┐         ┌────────▼─────────┐
│Fundamentals Svc │────────▶│  Analysis Service│
│  (hourly fetch) │  REST   │/ingest/fundamentals│
└─────────────────┘         └────────┬─────────┘
                                     │
                              ┌──────▼──────┐
                              │  Postgres   │
                              │   Database  │
                              └──────┬──────┘
                                     │
                              ┌──────▼──────┐
                              │  Dashboard  │
                              │  (Dash UI)  │
                              └─────────────┘
```

## API Endpoints

- `POST /ingest/prices` - Ingest price data
- `POST /ingest/fundamentals` - Ingest fundamentals data
- `GET /api/series/{ticker}` - Get price series with SMA20
- `GET /api/fundamentals/{ticker}` - Get fundamentals for a ticker

## Configuration

Environment variables (set in `.env`):
- `TICKERS`: Comma-separated list of stock tickers (default: AAPL,MSFT,GOOGL)
- `INTERVAL`: Price polling interval in seconds (default: 300 = 5 minutes)
- `REFRESH_SECONDS`: Fundamentals refresh interval (default: 3600 = 1 hour)

## Useful Commands

- **Start services:** `./start.sh` or `docker compose up --build`
- **View logs:** `docker compose logs -f`
- **View specific service logs:** `docker compose logs -f analysis`
- **Stop services:** `docker compose down`
- **Stop and remove volumes:** `docker compose down -v`
- **Rebuild a specific service:** `docker compose build analysis`

## Development

The project follows the structure outlined in `fundementals-service/prompt.txt` with:
- Clear data contracts (Pydantic schemas)
- Docker Compose for infrastructure
- SQLAlchemy for database models
- Structured logging with structlog
- Error handling with tenacity retries