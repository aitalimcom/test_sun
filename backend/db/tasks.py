"""Tasks and farm calendar database."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db.base import FileDB
from config import settings


class TasksDB(FileDB):
    """Manages farmer's scheduled tasks and agricultural calendar events."""

    def __init__(self) -> None:
        super().__init__(Path(settings.database_root) / "tasks", collection_name="tasks")

    def add_task(
        self,
        title: str,
        description: str = "",
        due_date: str | None = None,
        crop_type: str | None = None,
    ) -> dict[str, Any]:
        """Add a new task to the database."""
        task_id = f"task-{uuid.uuid4().hex[:12]}"
        record = {
            "id": task_id,
            "title": title,
            "description": description,
            "due_date": due_date or datetime.now(timezone.utc).date().isoformat(),
            "crop_type": crop_type,
            "completed": False,
            "completed_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save(task_id, record)
        return record

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        """Get a specific task."""
        return self.get(task_id)

    def list_tasks(self, limit: int = 50) -> list[dict[str, Any]]:
        """List all tasks sorted by due date."""
        tasks = self.list_all()
        # Sort by due_date
        return sorted(tasks, key=lambda t: t.get("due_date", ""))[:limit]

    def mark_completed(self, task_id: str, completed: bool = True) -> dict[str, Any] | None:
        """Toggle task completion state."""
        task = self.get(task_id)
        if not task:
            return None
        task["completed"] = completed
        task["completed_at"] = datetime.now(timezone.utc).isoformat() if completed else None
        self.save(task_id, task)
        return task


# Singleton
tasks_db = TasksDB()
