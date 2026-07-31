import logging
from fastapi import APIRouter, HTTPException
from typing import Any

from db.tasks import tasks_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])


@router.get("/tasks")
async def list_tasks() -> Any:
    """Get active tasks scheduled on the calendar."""
    return {"tasks": tasks_db.list_tasks()}


@router.post("/tasks")
async def add_task(title: str, description: str = "", due_date: str | None = None) -> Any:
    """Create a new schedule milestone on the calendar."""
    try:
        task = tasks_db.add_task(title=title, description=description, due_date=due_date)
        return {"status": "success", "task": task}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/complete")
async def mark_task_complete(task_id: str, completed: bool = True) -> Any:
    """Mark a task complete or pending."""
    task = tasks_db.mark_completed(task_id, completed=completed)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "task": task}
