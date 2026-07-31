"""
Feedback & Audit Database Manager.
Stores farmer audit feedback, bad responses, and reported conversations for model alignment.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db.base import FileDB
from config import settings


class FeedbackDB(FileDB):
    """Manages farmer response audits, bad feedback, and reported conversations."""

    def __init__(self) -> None:
        super().__init__(Path(settings.database_root) / "feedback", collection_name="feedback")

    def save_audit_feedback(
        self,
        query: str,
        answer: str,
        rating: str,  # 'good' | 'bad'
        reason: str = "",
        multimodal_context: dict[str, Any] | None = None,
        agent_name: str = "supervisor",
    ) -> dict[str, Any]:
        """Record farmer response audit feedback."""
        record_id = f"audit_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        # Sanitize PII
        cleaned_query = self._sanitize_pii(query)
        cleaned_answer = self._sanitize_pii(answer)

        record = {
            "id": record_id,
            "query": cleaned_query,
            "answer": cleaned_answer,
            "rating": rating,
            "reason": reason,
            "agent_name": agent_name,
            "multimodal_context": multimodal_context or {},
            "status": "reported" if rating == "bad" else "approved",
            "expert_correction": "",
            "created_at": now,
        }
        self.save(record_id, record)
        return record

    def list_reported_chats(self, limit: int = 100) -> list[dict[str, Any]]:
        """List reported chats flagged with bad feedback."""
        all_records = self.list_all(limit=limit * 2)
        reported = [r for r in all_records if r.get("rating") == "bad" or r.get("status") == "reported"]
        return reported[:limit]

    def update_expert_correction(self, record_id: str, expert_correction: str) -> dict[str, Any] | None:
        """Add expert correction to a reported conversation."""
        existing = self.get(record_id)
        if not existing:
            return None
        existing["expert_correction"] = expert_correction
        existing["status"] = "reviewed"
        existing["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save(record_id, existing)
        return existing

    def export_for_alignment(self) -> list[dict[str, Any]]:
        """Export reported chats into JSONL dataset format for model alignment/training."""
        all_records = feedback_db.list_reported_chats(limit=500)
        exported = []
        for r in all_records:
            exported.append({
                "instruction": r.get("query", ""),
                "input": json.dumps(r.get("multimodal_context", {})),
                "rejected_output": r.get("answer", ""),
                "chosen_output": r.get("expert_correction") or r.get("reason") or r.get("answer", ""),
                "metadata": {
                    "audit_id": r.get("id"),
                    "agent": r.get("agent_name"),
                    "created_at": r.get("created_at"),
                }
            })
        return exported

    def _sanitize_pii(self, text: str) -> str:
        """Sanitize citizenship numbers or phone numbers from feedback text."""
        import re
        if not text:
            return ""
        # Mask phone numbers (10 digits starting with 9)
        text = re.sub(r"\b9[78]\d{8}\b", "[PHONE_PROTECTED]", text)
        # Mask citizenship numbers
        text = re.sub(r"\b\d{2}-\d{2}-\d{2}-\d{5}\b", "[CITIZENSHIP_PROTECTED]", text)
        return text


# Singleton instance
feedback_db = FeedbackDB()
