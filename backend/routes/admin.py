from fastapi import APIRouter

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/eval")
async def run_eval():
    return {"message": "Eval endpoint — to be implemented"}


@router.get("/export")
async def export_data(format: str = "jsonl"):
    return {"format": format, "data": []}


@router.get("/cron")
async def list_cron_jobs():
    return {"jobs": []}
