"""Auditing and feedback database (for government portal auditing)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db.base import FileDB
from config import settings


class FeedbackDB(FileDB):
    """Stores farmer audit feedback on agent responses."""

    def __init__(self) -> None:
        super().__init__(Path(settings.database_root) / "feedback", collection_name="feedback")

    def submit_feedback(
        self,
        feedback_id: str,
        session_id: str,
        rating: int,  # 1 to 5, or binary
        comment: str = "",
        agent_trace: list[dict[str, Any]] | None = None,
        query: str = "",
        response_text: str = "",
    ) -> dict[str, Any]:
        """Record a farmer's response audit feedback."""
        record = {
            "feedback_id": feedback_id,
            "session_id": session_id,
            "rating": rating,
            "comment": comment,
            "agent_trace": agent_trace or [],
            "query": query,
            "response_text": response_text,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "reviewed": False,  # Goverment review status
        }
        self.save(feedback_id, record)
        return record

    def list_pending_reviews(self, limit: int = 50) -> list[dict[str, Any]]:
        """List feedback submissions that government admins haven't reviewed yet."""
        feedback = self.list_all()
        return [f for f in feedback if not f.get("reviewed", False)][:limit]


# Singleton
feedback_db = FeedbackDB()
