from fastapi import APIRouter

router = APIRouter(prefix="/api/market", tags=["market"])


@router.get("/prices")
async def get_prices(market: str = "kalimati"):
    return {"market": market, "prices": []}


@router.get("/trends/{crop}")
async def get_trends(crop: str):
    return {"crop": crop, "trends": []}
