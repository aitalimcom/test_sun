"""
Community Q&A Database Manager.
Stores farmer community questions, expert/community answers, saves, and feedback.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db.base import FileDB
from config import settings


class CommunityDB(FileDB):
    """Manages farmer community forum questions, answers, and bookmarks."""

    def __init__(self) -> None:
        super().__init__(Path(settings.database_root) / "community", collection_name="community")

    def create_post(
        self,
        author: str,
        question: str,
        crop_tag: str = "सामान्य",
        location: str = "नेपाल",
        image_path: str | None = None,
    ) -> dict[str, Any]:
        """Create a new farmer community question post."""
        post_id = f"post_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        
        record = {
            "id": post_id,
            "author": author or "कृषक मित्र",
            "question": question,
            "crop_tag": crop_tag,
            "location": location,
            "image_path": image_path,
            "answers": [],
            "saves_count": 0,
            "created_at": now,
        }
        self.save(post_id, record)
        return record

    def add_answer(self, post_id: str, author: str, answer_text: str, is_gemma_ai: bool = False) -> dict[str, Any] | None:
        """Add an answer to a community question."""
        post = self.get(post_id)
        if not post:
            return None

        ans_entry = {
            "id": f"ans_{uuid.uuid4().hex[:8]}",
            "author": author,
            "answer_text": answer_text,
            "is_gemma_ai": is_gemma_ai,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        post.setdefault("answers", []).append(ans_entry)
        self.save(post_id, post)
        return post

    def list_posts(self, crop_tag: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """List community posts, optionally filtered by crop tag."""
        records = self.list_all(limit=limit)
        if crop_tag:
            records = [r for r in records if crop_tag.lower() in r.get("crop_tag", "").lower()]
        return records

    def toggle_save_post(self, post_id: str) -> dict[str, Any] | None:
        """Increment bookmark save count for a question."""
        post = self.get(post_id)
        if not post:
            return None
        post["saves_count"] = post.get("saves_count", 0) + 1
        self.save(post_id, post)
        return post


# Singleton instance
community_db = CommunityDB()
