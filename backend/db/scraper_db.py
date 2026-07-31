"""
SQLite Staging Database Manager for Government Web Scraper & RAG Ingestion Pipeline.
Stores crawled URLs, frontier queue, dead letters, and pending scraped documents (PDFs, Images, HTML).
"""

from __future__ import annotations

import sqlite3
import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import settings

logger = logging.getLogger(__name__)

DB_PATH = Path(settings.database_root) / "scraped.db"


class ScraperDB:
    """SQLite Database manager for web crawling & RAG document staging."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS visited (
                    url TEXT PRIMARY KEY,
                    visited_at DATETIME
                );

                CREATE TABLE IF NOT EXISTS frontier (
                    url TEXT PRIMARY KEY,
                    added_at DATETIME
                );

                CREATE TABLE IF NOT EXISTS dead_letter (
                    url TEXT PRIMARY KEY,
                    reason TEXT,
                    failed_at DATETIME
                );

                CREATE TABLE IF NOT EXISTS scraped_documents (
                    id TEXT PRIMARY KEY,
                    url TEXT UNIQUE,
                    title TEXT,
                    file_type TEXT, -- pdf, image, html
                    file_path TEXT,
                    file_size_bytes INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'scraped', -- scraped, inspected, ingested, rejected
                    is_preeti INTEGER DEFAULT 0,
                    is_agriculture INTEGER DEFAULT 1,
                    relevance_reason TEXT DEFAULT '',
                    raw_text TEXT DEFAULT '',
                    converted_text TEXT DEFAULT '',
                    summary TEXT DEFAULT '',
                    category TEXT DEFAULT 'diseases', -- diseases, practices, guides, gallery
                    scraped_at DATETIME,
                    updated_at DATETIME
                );
            """)
            conn.commit()

    # ── Crawl Frontier Management ──

    def add_frontier(self, url: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO frontier (url, added_at) VALUES (?, ?)", (url, now))
            conn.commit()

    def mark_visited(self, url: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("DELETE FROM frontier WHERE url = ?", (url,))
            conn.execute("INSERT OR REPLACE INTO visited (url, visited_at) VALUES (?, ?)", (url, now))
            conn.commit()

    def mark_dead_letter(self, url: str, reason: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute("DELETE FROM frontier WHERE url = ?", (url,))
            conn.execute("INSERT OR REPLACE INTO dead_letter (url, reason, failed_at) VALUES (?, ?, ?)", (url, reason, now))
            conn.commit()

    def is_visited_or_dead(self, url: str) -> bool:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT 1 FROM visited WHERE url = ? UNION SELECT 1 FROM dead_letter WHERE url = ?", (url, url))
            return cur.fetchone() is not None

    # ── Scraped Document Staging CRUD ──

    def save_scraped_document(
        self,
        url: str,
        title: str,
        file_type: str,
        file_path: str,
        file_size_bytes: int = 0,
        status: str = "scraped",
        category: str = "diseases",
    ) -> dict[str, Any]:
        """Save a new scraped document record in SQLite staging."""
        now = datetime.now(timezone.utc).isoformat()
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM scraped_documents WHERE url = ?", (url,))
            existing = cur.fetchone()
            if existing:
                return dict(existing)

            conn.execute(
                """
                INSERT INTO scraped_documents 
                (id, url, title, file_type, file_path, file_size_bytes, status, category, scraped_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (doc_id, url, title, file_type, file_path, file_size_bytes, status, category, now, now),
            )
            conn.commit()

        return self.get_document(doc_id) or {}

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """Fetch a single scraped document by ID."""
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM scraped_documents WHERE id = ?", (doc_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def list_scraped_documents(self, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """List scraped documents, optionally filtered by status."""
        with self._get_connection() as conn:
            if status:
                cur = conn.execute(
                    "SELECT * FROM scraped_documents WHERE status = ? ORDER BY scraped_at DESC LIMIT ?",
                    (status, limit),
                )
            else:
                cur = conn.execute(
                    "SELECT * FROM scraped_documents ORDER BY scraped_at DESC LIMIT ?",
                    (limit,),
                )
            return [dict(r) for r in cur.fetchall()]

    def update_document_inspection(
        self,
        doc_id: str,
        raw_text: str,
        converted_text: str,
        is_preeti: bool,
        is_agriculture: bool,
        relevance_reason: str,
        summary: str = "",
        category: str = "diseases",
    ) -> dict[str, Any] | None:
        """Update inspection results from Gemma 4."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE scraped_documents
                SET raw_text = ?, converted_text = ?, is_preeti = ?, is_agriculture = ?,
                    relevance_reason = ?, summary = ?, category = ?, status = 'inspected', updated_at = ?
                WHERE id = ?
                """,
                (
                    raw_text,
                    converted_text,
                    1 if is_preeti else 0,
                    1 if is_agriculture else 0,
                    relevance_reason,
                    summary,
                    category,
                    now,
                    doc_id,
                ),
            )
            conn.commit()
        return self.get_document(doc_id)

    def mark_ingested(self, doc_id: str, category: str | None = None) -> bool:
        """Mark document status as ingested into RAG Knowledge Base."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            if category:
                conn.execute(
                    "UPDATE scraped_documents SET status = 'ingested', category = ?, updated_at = ? WHERE id = ?",
                    (category, now, doc_id),
                )
            else:
                conn.execute(
                    "UPDATE scraped_documents SET status = 'ingested', updated_at = ? WHERE id = ?",
                    (now, doc_id),
                )
            conn.commit()
            return True

    def mark_rejected(self, doc_id: str, reason: str = "") -> bool:
        """Mark document status as rejected."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE scraped_documents SET status = 'rejected', relevance_reason = ?, updated_at = ? WHERE id = ?",
                (reason, now, doc_id),
            )
            conn.commit()
            return True


# Singleton instance
scraper_db = ScraperDB()
