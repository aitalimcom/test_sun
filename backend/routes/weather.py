from fastapi import APIRouter

router = APIRouter(prefix="/api/weather", tags=["weather"])


@router.get("/current")
async def current_weather(lat: float = 27.7172, lng: float = 85.3240):
    return {"lat": lat, "lng": lng, "temperature": None, "condition": None}
