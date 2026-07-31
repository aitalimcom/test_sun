"""Conversation memory management — file-backed session storage."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from config import settings

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation history backed by the file-system DB.

    Each session is a JSON file containing:
    - session_id
    - messages: list of {role, content, metadata, timestamp}
    - created_at, updated_at
    """

    def __init__(self) -> None:
        self.base_dir = Path(settings.database_root) / "chat_history"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"

    def create_session(self, session_id: str, language: str = "ne-NP") -> dict[str, Any]:
        """Create a new chat session."""
        session = {
            "id": session_id,
            "language": language,
            "messages": [],
            "created_at": self._now_iso(),
            "updated_at": self._now_iso(),
        }
        self._save(session)
        logger.info(f"Created session: {session_id}")
        return session

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Load a session by ID."""
        path = self._session_path(session_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_or_create_session(self, session_id: str, language: str = "ne-NP") -> dict[str, Any]:
        """Get existing session or create new one."""
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
            session_id: The session to append to.
            role: "user" | "assistant" | "system"
            content: Message text.
            metadata: Optional metadata (tool_calls, verdict, latency, etc.).

        Returns:
            The created message dict.
        """
        session = self.get_or_create_session(session_id)
        message = {
            "role": role,
            "content": content,
            "timestamp": self._now_iso(),
            "metadata": metadata or {},
        }
        session["messages"].append(message)
        session["updated_at"] = self._now_iso()
        self._save(session)
        return message

    def get_history(
        self,
        session_id: str,
        limit: int = 50,
        include_metadata: bool = False,
    ) -> list[dict[str, Any]]:
        """Get message history for a session.

        Args:
            session_id: The session to get history for.
            limit: Maximum number of messages to return.
            include_metadata: Whether to include metadata in output.

        Returns:
            List of message dicts (most recent last).
        """
        session = self.get_session(session_id)
        if not session:
            return []

        messages = session["messages"][-limit:]

        if not include_metadata:
            return [
                {"role": m["role"], "content": m["content"]}
                for m in messages
            ]

        return messages

    def list_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        """List recent sessions."""
        sessions = []
        if not self.base_dir.exists():
            return []
        for path in sorted(self.base_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
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

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        path = self._session_path(session_id)
        if path.exists():
            path.unlink()
            logger.info(f"Deleted session: {session_id}")
            return True
        return False

    def _save(self, session: dict[str, Any]) -> None:
        """Persist session to disk."""
        path = self._session_path(session["id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session, f, indent=2, ensure_ascii=False, default=str)

    @staticmethod
    def _now_iso() -> str:
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


# Singleton
conversation_memory = ConversationMemory()
