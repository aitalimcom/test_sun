"""Document indexer — loads knowledge base docs into ChromaDB."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from config import settings

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """Indexes knowledge base documents into the vector store."""

    def __init__(self) -> None:
        self.knowledge_dir = Path(settings.database_root) / "knowledge"

    async def index_all(self, force: bool = False) -> int:
        """Index all knowledge base documents.

        Args:
            force: If True, re-index even if already indexed.

        Returns:
            Number of documents indexed.
        """
        try:
            from langchain_community.document_loaders import DirectoryLoader, TextLoader
            from langchain.text_splitter import RecursiveCharacterTextSplitter

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", ". ", " "],
            )

            all_docs = []
            for category in ["diseases", "practices", "guides"]:
                cat_dir = self.knowledge_dir / category
                if not cat_dir.exists():
                    continue

                loader = DirectoryLoader(
                    str(cat_dir),
                    glob="**/*.md",
                    loader_cls=TextLoader,
                    loader_kwargs={"encoding": "utf-8"},
                )
                docs = loader.load()

                # Add category metadata
                for doc in docs:
                    doc.metadata["category"] = category

                chunks = splitter.split_documents(docs)
                all_docs.extend(chunks)
                logger.info(f"Loaded {len(chunks)} chunks from {category}")

            if all_docs:
                from services.rag.vectorstore import vectorstore_manager
                store = await vectorstore_manager.get_or_create()
                await vectorstore_manager.add_documents(all_docs)
                logger.info(f"Indexed {len(all_docs)} total chunks")
                return len(all_docs)

            return 0

        except Exception as e:
            logger.error(f"Document indexing failed: {e}")
            return 0

    def get_stats(self) -> dict[str, Any]:
        """Get knowledge base stats."""
        stats = {"diseases": 0, "practices": 0, "guides": 0, "total": 0}
        for category in ["diseases", "practices", "guides"]:
            cat_dir = self.knowledge_dir / category
            if cat_dir.exists():
                count = len(list(cat_dir.glob("*.md")))
                stats[category] = count
                stats["total"] += count
        return stats


# Singleton
document_indexer = DocumentIndexer()
