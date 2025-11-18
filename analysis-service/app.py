from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from src.db import init_db, Prices, Fundamentals, SessionLocal
from src.indicators import sma
from src.dash_app import mount_dash

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    mount_dash(app)  # mounts Dash at "/"
    yield
    # Shutdown (if needed)

app = FastAPI(title="Analysis Service", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/ingest/prices")
def ingest_prices(payload: dict):
    try:
        from dateutil import parser
        with SessionLocal() as s:
            for p in payload["points"]:
                # Parse ISO timestamp string to datetime
                ts = parser.isoparse(p["ts"]) if isinstance(p["ts"], str) else p["ts"]
                s.merge(Prices(
                    ticker=payload["ticker"],
                    ts=ts, open=p["open"], high=p["high"],
                    low=p["low"], close=p["close"], volume=p["volume"]))
            s.commit()
        return {"status": "ok", "count": len(payload["points"])}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ingest/fundamentals")
def ingest_fundamentals(payload: dict):
    try:
        from datetime import datetime
        m = payload["metrics"]
        with SessionLocal() as s:
            # Parse date string if needed
            as_of = payload["as_of"]
            if isinstance(as_of, str):
                from dateutil import parser
                as_of = parser.parse(as_of).date()
            s.merge(Fundamentals(
                ticker=payload["ticker"], as_of=as_of,
                pe_ttm=m.get("pe_ttm"), market_cap=m.get("market_cap"),
                fifty_two_week_high=m.get("fifty_two_week_high"),
                fifty_two_week_low=m.get("fifty_two_week_low")))
            s.commit()
        return {"status":"ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/series/{ticker}")
def series(ticker: str, window: int = 200):
    with SessionLocal() as s:
        rows = s.query(Prices).filter(Prices.ticker==ticker).order_by(Prices.ts.desc()).limit(window).all()
        payload = [{"ts": r.ts.isoformat() if hasattr(r.ts, 'isoformat') else str(r.ts), "close": float(r.close)} for r in reversed(rows)]
        closes = [p["close"] for p in payload]
        payload_sma20 = sma(closes, 20) if closes else []
        return {"points": payload, "sma20": payload_sma20}

@app.get("/api/fundamentals/{ticker}")
def fundamentals(ticker: str):
    with SessionLocal() as s:
        f = s.get(Fundamentals, ticker)
        if not f: raise HTTPException(404, "No fundamentals")
        return {
          "ticker": ticker, "as_of": str(f.as_of),
          "pe_ttm": float(f.pe_ttm) if f.pe_ttm is not None else None,
          "market_cap": float(f.market_cap) if f.market_cap is not None else None,
          "fifty_two_week_high": float(f.fifty_two_week_high) if f.fifty_two_week_high else None,
          "fifty_two_week_low": float(f.fifty_two_week_low) if f.fifty_two_week_low else None
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(8050))

