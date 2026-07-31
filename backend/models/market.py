from pydantic import BaseModel
from typing import List, Optional


class MarketPrice(BaseModel):
    crop: str
    min_price: float
    max_price: float
    unit: str = "KG"
    market: str = "kalimati"


class MarketPriceResponse(BaseModel):
    market: str
    prices: List[MarketPrice]
    updated_at: str
