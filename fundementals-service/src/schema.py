from pydantic import BaseModel
from typing import Optional

class FundamentalsMetrics(BaseModel):
    pe_ttm: Optional[float] = None
    market_cap: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None

class FundamentalsPayload(BaseModel):
    ticker: str
    provider: str
    as_of: str
    metrics: FundamentalsMetrics


