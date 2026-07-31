from fastapi import APIRouter

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/")
async def chat():
    return {"message": "Chat endpoint — to be implemented"}


@router.get("/sessions")
async def list_sessions():
    return {"sessions": []}
