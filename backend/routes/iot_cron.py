"""Cron management API."""
import logging
from fastapi import APIRouter, HTTPException
from typing import Any

from core.cron import cron_scheduler
from models.iot import CronJobUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/iot/cron", tags=["IoT Cron"])


@router.get("/jobs")
async def list_cron_jobs() -> Any:
    return {"jobs": cron_scheduler.get_status()}


@router.post("/jobs/{job_name}/toggle")
async def toggle_cron_job(job_name: str, req: CronJobUpdate) -> Any:
    if cron_scheduler.toggle(job_name, req.enabled):
        status = "enabled" if req.enabled else "disabled"
        return {"message": f"Cron job '{job_name}' {status}"}
    raise HTTPException(status_code=404, detail="Job not found")


@router.post("/trigger/{job_name}")
async def trigger_cron_job(job_name: str) -> Any:
    """Manually trigger a cron job."""
    job = cron_scheduler.jobs.get(job_name)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    import asyncio
    await cron_scheduler._run_job(job)
    return {"message": f"Job '{job_name}' triggered manually"}
