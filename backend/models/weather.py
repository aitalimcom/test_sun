from pydantic import BaseModel
from typing import Optional


class WeatherResponse(BaseModel):
    lat: float
    lng: float
    current: str
    forecast: str
    spray_recommendation: Optional[str] = None
