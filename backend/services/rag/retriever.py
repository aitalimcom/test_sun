"""RAG retriever — queries ChromaDB for relevant knowledge."""

from __future__ import annotations

import logging
from typing import Any

from core.exceptions import RAGNotReadyError

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieves relevant documents from the vector store."""

    def __init__(self) -> None:
        self._vectorstore = None
        self._retriever = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the ChromaDB vector store and retriever."""
        if self._initialized:
            return

        try:
            from services.rag.vectorstore import vectorstore_manager
            self._vectorstore = await vectorstore_manager.get_or_create()
            self._retriever = self._vectorstore.as_retriever(
                search_kwargs={"k": 3}
            )
            self._initialized = True
            logger.info("RAG retriever initialized")
        except Exception as e:
            logger.warning(f"RAG initialization failed: {e}")
            self._initialized = False

    async def retrieve(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Retrieve matches for compatibility with get_latest / query endpoints."""
        res = await self.query(query, top_k=limit)
        return res.get("documents", [])

    async def query(
        self,
        question: str,
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query the knowledge base.

        Args:
            question: The search query.
            top_k: Number of results to return.
            filters: Optional metadata filters.

        Returns:
            Dict with 'documents' and 'citations' keys.
        """
        await self.initialize()

        if not self._initialized or not self._retriever:
            return {"documents": [], "citations": []}

        try:
            docs = await self._retriever.ainvoke(question)

            documents = []
            citations = []
            for i, doc in enumerate(docs[:top_k]):
                doc_info = {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "Unknown"),
                    "category": doc.metadata.get("category", ""),
                    "doc_title": Path(doc.metadata.get("source", "Unknown")).stem if doc.metadata.get("source") else "Unknown",
                    "score": doc.metadata.get("score", 0.9 - (i * 0.1)),  # Approximate ranking
                }
                documents.append(doc_info)
                citations.append({
                    "doc_id": doc_info["doc_title"],
                    "doc_title": doc_info["doc_title"],
                    "score": doc_info["score"],
                    "snippet": doc_info["content"][:200],
                    "chunk_index": i,
                })

            return {"documents": documents, "citations": citations}

        except Exception as e:
            logger.error(f"RAG query failed: {e}")
            return {"documents": [], "citations": []}

    def is_ready(self) -> bool:
        """Check if RAG is initialized and ready."""
        return self._initialized and self._retriever is not None


from pathlib import Path

# Singleton
rag_retriever = RAGRetriever()
