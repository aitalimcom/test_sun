"""File-system database base class — wraps file operations with error handling."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from core.exceptions import DBError, DBNotFoundError

logger = logging.getLogger(__name__)


class FileDB:
    """Simple file-system JSON database with proper error handling."""

    def __init__(self, base_dir: Path, collection_name: str = "default"):
        self.base_dir = Path(base_dir)
        self.collection_name = collection_name
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, record_id: str) -> Path:
        return self.base_dir / f"{record_id}.json"

    def save(self, record_id: str, data: dict[str, Any]) -> None:
        """Save a record."""
        try:
            path = self._path(record_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            raise DBError(self.collection_name, f"save failed: {e}") from e

    def get(self, record_id: str) -> dict[str, Any] | None:
        """Get a record by ID. Returns None if not found."""
        path = self._path(record_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read {record_id}: {e}")
            return None

    def get_or_raise(self, record_id: str) -> dict[str, Any]:
        """Get a record by ID. Raises DBNotFoundError if not found."""
        record = self.get(record_id)
        if record is None:
            raise DBNotFoundError(self.collection_name, record_id)
        return record

    def delete(self, record_id: str) -> bool:
        """Delete a record. Returns True if deleted."""
        path = self._path(record_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_all(self, limit: int | None = None) -> list[dict[str, Any]]:
        """List all records, optionally limited."""
        records = []
        for path in sorted(self.base_dir.glob("*.json")):
            if path.name.startswith("_"):
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    records.append(json.load(f))
            except (json.JSONDecodeError, IOError):
                continue
            if limit and len(records) >= limit:
                break
        return records

    def search(self, field: str, value: Any) -> list[dict[str, Any]]:
        """Simple search by field value."""
        return [r for r in self.list_all() if r.get(field) == value]

    def count(self) -> int:
        """Count records."""
        return len(list(self.base_dir.glob("*.json"))) - len(
            list(self.base_dir.glob("_*.json"))
        )

    def exists(self, record_id: str) -> bool:
        """Check if a record exists."""
        return self._path(record_id).exists()
