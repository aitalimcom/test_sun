"""Knowledge base database — manages source documents for RAG."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from config import settings


class KnowledgeDB:
    """Manages the agricultural knowledge base documents.

    Documents are stored as Markdown files in:
        database/knowledge/diseases/
        database/knowledge/practices/
        database/knowledge/guides/
    """

    def __init__(self) -> None:
        self.base_dir = Path(settings.database_root) / "knowledge"

    def list_documents(self, category: str | None = None) -> list[dict[str, Any]]:
        """List all knowledge documents."""
        docs = []
        categories = [category] if category else ["diseases", "practices", "guides"]

        for cat in categories:
            cat_dir = self.base_dir / cat
            if not cat_dir.exists():
                continue
            for path in cat_dir.glob("*.md"):
                docs.append({
                    "id": path.stem,
                    "category": cat,
                    "filename": path.name,
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                })
        return docs

    def get_document(self, category: str, doc_id: str) -> str | None:
        """Read a knowledge document's content."""
        path = self.base_dir / category / f"{doc_id}.md"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def get_stats(self) -> dict[str, Any]:
        """Get stats about the knowledge base."""
        stats = {"diseases": 0, "practices": 0, "guides": 0, "total": 0}
        for cat in ["diseases", "practices", "guides"]:
            cat_dir = self.base_dir / cat
            if cat_dir.exists():
                count = len(list(cat_dir.glob("*.md")))
                stats[cat] = count
                stats["total"] += count
        return stats


# Singleton
knowledge_db = KnowledgeDB()
