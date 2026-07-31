"""Hybrid RAG Retriever — Combines BM25 Lexical Ranking with Dense ChromaDB Vector Search."""

from __future__ import annotations

import logging
from typing import Any
from rank_bm25 import BM25Okapi

from core.normalizer import normalize_nepali_text
from services.rag.vectorstore import vectorstore_manager

logger = logging.getLogger(__name__)


class HybridRAGRetriever:
    """Hybrid Search engine performing sparse (BM25) + dense (ChromaDB) retrieval."""

    def __init__(self) -> None:
        self._bm25 = None
        self._corpus_docs: list[dict[str, Any]] = []
        self._initialized = False

    def index_corpus(self, docs: list[dict[str, Any]]) -> None:
        """Build the BM25 index from a list of document dicts.

        Each doc in docs should have: 'content', 'source', 'title', 'category'.
        """
        self._corpus_docs = docs
        tokenized_corpus = []

        for doc in docs:
            text = doc.get("content", "")
            # Normalize Nepali text (Hraswa/Dirga, S/N) before tokenizing for BM25
            norm_text = normalize_nepali_text(text)
            tokens = norm_text.split()
            tokenized_corpus.append(tokens)

        if tokenized_corpus:
            self._bm25 = BM25Okapi(tokenized_corpus)
            self._initialized = True
            logger.info(f"BM25 index built with {len(docs)} document chunks.")

    async def retrieve(
        self,
        query: str,
        limit: int = 4,
        alpha: float = 0.5,
    ) -> list[dict[str, Any]]:
        """Perform hybrid retrieval.

        Args:
            query: The user query.
            limit: Top-k items to return.
            alpha: Weight ratio between BM25 (alpha) and Dense vector (1 - alpha).

        Returns:
            List of documents with combined relevance scores.
        """
        norm_query = normalize_nepali_text(query)
        query_tokens = norm_query.split()

        # 1. Sparse BM25 Search
        bm25_scores = {}
        if self._bm25 and query_tokens:
            raw_scores = self._bm25.get_scores(query_tokens)
            max_s = max(raw_scores) if max(raw_scores) > 0 else 1.0
            for idx, score in enumerate(raw_scores):
                if score > 0:
                    bm25_scores[idx] = score / max_s  # Normalize 0.0 to 1.0

        # 2. Dense Vector Search (ChromaDB)
        dense_results = []
        try:
            dense_results = await vectorstore_manager.search(query, k=limit * 2)
        except Exception as e:
            logger.warning(f"ChromaDB search error: {e}")

        # Combine results into a map by content hash / title
        combined = {}

        # Add Dense results
        for idx, doc in enumerate(dense_results):
            content = doc.page_content if hasattr(doc, "page_content") else doc.get("content", "")
            meta = doc.metadata if hasattr(doc, "metadata") else doc.get("metadata", {})
            title = meta.get("source", "Wiki")
            
            dense_score = 0.9 - (idx * 0.1)  # Approximate dense score rank
            combined[content] = {
                "content": content,
                "source": meta.get("source", "Knowledge Base"),
                "category": meta.get("category", "guides"),
                "model_used": meta.get("model_used", "gemma-4"),
                "doc_title": title,
                "score": (1 - alpha) * dense_score,
            }

        # Add BM25 results
        for idx, score in bm25_scores.items():
            if idx < len(self._corpus_docs):
                cdoc = self._corpus_docs[idx]
                content = cdoc.get("content", "")
                
                existing = combined.get(content, {
                    "content": content,
                    "source": cdoc.get("source", "Knowledge Base"),
                    "category": cdoc.get("category", "guides"),
                    "model_used": cdoc.get("model_used", "gemma-4"),
                    "doc_title": cdoc.get("title", "Knowledge Base"),
                    "score": 0.0,
                })
                existing["score"] += alpha * score
                combined[content] = existing

        # Sort combined results by highest score
        ranked = sorted(combined.values(), key=lambda x: x["score"], reverse=True)
        return ranked[:limit]


# Singleton
hybrid_retriever = HybridRAGRetriever()
