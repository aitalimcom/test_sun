"""Raw source text files manager."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from config import settings

logger = logging.getLogger(__name__)


class SourceDB:
    """Manages raw extracted text files saved in database/source/."""

    def __init__(self) -> None:
        self.base_dir = Path(settings.database_root) / "source"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_source(self, doc_id: str, content: str, metadata: dict[str, Any] | None = None) -> Path:
        """Save extracted source text."""
        path = self.base_dir / f"{doc_id}.txt"
        path.write_text(content, encoding="utf-8")
        
        # Optionally save metadata alongside
        if metadata:
            import json
            meta_path = self.base_dir / f"{doc_id}.json"
            meta_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
            
        logger.info(f"Saved raw source text: {path}")
        return path

    def get_source(self, doc_id: str) -> str | None:
        """Get raw source text by doc_id."""
        path = self.base_dir / f"{doc_id}.txt"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def list_sources(self) -> list[dict[str, Any]]:
        """List all saved source files."""
        sources = []
        for path in sorted(self.base_dir.glob("*.txt")):
            sources.append({
                "id": path.stem,
                "filename": path.name,
                "size_bytes": path.stat().st_size,
                "path": str(path),
            })
        return sources


# Singleton
source_db = SourceDB()
