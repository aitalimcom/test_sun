"""ChromaDB vector store manager."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from config import settings

logger = logging.getLogger(__name__)

# Persistent storage path
CHROMA_DIR = Path(settings.database_root) / "chromadb"


class VectorstoreManager:
    """Manages the ChromaDB vector store for agricultural knowledge."""

    def __init__(self) -> None:
        self._vectorstore = None

    async def get_or_create(self) -> Any:
        """Get or create the ChromaDB vector store."""
        if self._vectorstore is not None:
            return self._vectorstore

        try:
            import chromadb
            from langchain_community.vectorstores import Chroma
            from langchain_community.embeddings import HuggingFaceEmbeddings

            CHROMA_DIR.mkdir(parents=True, exist_ok=True)

            embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
            )

            self._vectorstore = Chroma(
                collection_name="krishimitra_knowledge",
                embedding_function=embeddings,
                persist_directory=str(CHROMA_DIR),
            )

            logger.info(f"ChromaDB initialized at {CHROMA_DIR}")
            return self._vectorstore

        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            raise

    async def add_documents(self, documents: list[Any]) -> None:
        """Add documents to the vector store."""
        store = await self.get_or_create()
        if store and documents:
            store.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to vector store")

    async def search(self, query: str, k: int = 3) -> list[Any]:
        """Search the vector store."""
        store = await self.get_or_create()
        if not store:
            return []
        return store.similarity_search(query, k=k)


# Singleton
vectorstore_manager = VectorstoreManager()
