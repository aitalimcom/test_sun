from fastapi import APIRouter

router = APIRouter(prefix="/api/doctor", tags=["doctor"])


@router.post("/diagnose")
async def diagnose():
    return {"message": "Diagnose endpoint — to be implemented"}


@router.get("/history")
async def diagnosis_history():
    return {"history": []}
