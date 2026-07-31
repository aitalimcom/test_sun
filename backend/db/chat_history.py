"""Chat history database — session + message management."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db.base import FileDB
from config import settings


class ChatHistoryDB(FileDB):
    """Manages chat sessions and messages.

    Storage structure:
        database/chat_history/
            {session_id}.json  →  { id, language, messages: [...], created_at, updated_at }
    """

    def __init__(self) -> None:
        super().__init__(Path(settings.database_root) / "chat_history", collection_name="chat_history")

    def create_session(self, session_id: str, language: str = "ne-NP") -> dict[str, Any]:
        """Create a new chat session."""
        session = {
            "id": session_id,
            "language": language,
            "messages": [],
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.save(session_id, session)
        return session

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get a session by ID."""
        return self.get(session_id)

    def get_or_create_session(self, session_id: str, language: str = "ne-NP") -> dict[str, Any]:
        """Get or create a session."""
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id, language)
        return session

    def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Append a message to a session.

        Args:
            session_id: Target session.
            role: "user" | "assistant" | "system".
            content: Message text.
            metadata: Optional metadata (tool_calls, verdict, latency, etc.).

        Returns:
            The created message dict.
        """
        session = self.get_or_create_session(session_id)
        message = {
            "role": role,
            "content": content,
            "timestamp": self._now(),
            "metadata": metadata or {},
        }
        session["messages"].append(message)
        session["updated_at"] = self._now()
        self.save(session_id, session)
        return message

    def get_history(
        self,
        session_id: str,
        limit: int = 50,
        include_metadata: bool = False,
    ) -> list[dict[str, Any]]:
        """Get message history for a session."""
        session = self.get_session(session_id)
        if not session:
            return []

        messages = session["messages"][-limit:]

        if not include_metadata:
            return [{"role": m["role"], "content": m["content"]} for m in messages]
        return messages

    def list_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent sessions (summary only)."""
        sessions = []
        for path in sorted(
            self.base_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            if path.name.startswith("_"):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "id": data.get("id"),
                    "language": data.get("language"),
                    "message_count": len(data.get("messages", [])),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                })
            except (json.JSONDecodeError, KeyError):
                continue
            if len(sessions) >= limit:
                break
        return sessions

    def get_last_assistant_message(self, session_id: str) -> str | None:
        """Get the most recent assistant message content."""
        history = self.get_history(session_id, limit=10)
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                return msg.get("content")
        return None

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


# Singleton
chat_history_db = ChatHistoryDB()
