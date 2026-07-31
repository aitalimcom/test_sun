"""OpenWeatherMap API service wrapper."""

from __future__ import annotations

import logging
import httpx
from typing import Any
from config import settings

logger = logging.getLogger(__name__)


class WeatherService:
    """Queries OpenWeatherMap API for live coordinates or falls back to mock data."""

    def __init__(self) -> None:
        self.api_key = settings.openweather_api_key

    async def get_weather_and_forecast(self, lat: float, lon: float) -> dict[str, Any] | None:
        """Fetch current weather and forecast. Fallback to mock if API key is missing."""
        if not self.api_key or self.api_key == "your-key-here":
            logger.info("OpenWeatherMap API key not found. Using mock weather.")
            return self._get_mock_weather(lat, lon)

        try:
            url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={self.api_key}&units=metric&lang=np"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                
                # Parse current conditions
                first_item = data.get("list", [{}])[0]
                temp = first_item.get("main", {}).get("temp", 25.0)
                humidity = first_item.get("main", {}).get("humidity", 70)
                wind = first_item.get("wind", {}).get("speed", 5.0)
                description = first_item.get("weather", [{}])[0].get("description", "आंशिक बदली")
                
                current_str = f"तापक्रम: {temp}°C, अवस्था: {description}, सापेक्षित आद्रता: {humidity}%, हावाको गति: {wind} कि.मी./घण्टा"
                
                # Construct 3 day forecast summary
                forecast_lines = []
                # Daily averages or items at 24h intervals
                for i, item in enumerate(data.get("list", [])[8:32:8]):
                    f_temp = item.get("main", {}).get("temp", 25.0)
                    f_desc = item.get("weather", [{}])[0].get("description", "आंशिक बदली")
                    forecast_lines.append(f"दिन {i+1}: तापक्रम {f_temp}°C, {f_desc}")
                
                forecast_str = "\n".join(forecast_lines)
                
                return {
                    "current_str": current_str,
                    "forecast_str": forecast_str,
                    "raw": data
                }
        except Exception as e:
            logger.error(f"OpenWeatherMap API request failed: {e}. Falling back to mock weather.")
            return self._get_mock_weather(lat, lon)

    def _get_mock_weather(self, lat: float, lon: float) -> dict[str, Any]:
        return {
            "current_str": "तापक्रम: २६.२°C, अवस्था: आंशिक बदली, सापेक्षित आद्रता: ७४%, हावाको गति: ७ कि.मी./घण्टा",
            "forecast_str": (
                "दिन १: तापक्रम २७°C, हल्का वर्षाको सम्भावना\n"
                "दिन २: तापक्रम २६°C, मौसम सफा रहने\n"
                "दिन ३: तापक्रम २८°C, आंशिक बदली"
            ),
            "raw": {}
        }


# Singleton
weather_service = WeatherService()
