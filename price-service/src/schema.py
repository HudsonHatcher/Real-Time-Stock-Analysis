from pydantic import BaseModel
from typing import List
from datetime import datetime

class PricePoint(BaseModel):
    ts: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class PricePayload(BaseModel):
    ticker: str
    provider: str
    interval: str
    points: List[PricePoint]


