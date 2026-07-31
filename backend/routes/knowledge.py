from fastapi import APIRouter

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/search")
async def search_knowledge(q: str, crop: str | None = None):
    return {"query": q, "crop": crop, "results": []}
