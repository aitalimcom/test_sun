"""
Government Agriculture Web Scraper Service with SQLite Staging Database.
Crawls Nepali agricultural government sites and saves discovered PDFs, images, and HTML documents
into SQLite staging (`database/scraped.db`) for human-in-the-loop inspection and RAG ingestion.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import pypdf
import io
from pathlib import Path
from typing import Any
import httpx
from bs4 import BeautifulSoup
from yarl import URL

from config import settings
from db.scraper_db import scraper_db
from core.preeti import is_preeti_text, preeti_to_unicode

logger = logging.getLogger(__name__)

TARGET_SEEDS = [
    "https://moald.gov.np",
    "https://doanepal.gov.np",
    "https://pmamp.gov.np",
    "https://aitc.gov.np",
    "https://doad.bagamati.gov.np",
    "https://www.asdp.gov.np",
]

ALLOWED_DOMAINS = (".gov.np", ".edu.np", ".org.np")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class GovAgricultureScraper:
    """Async web crawler saving documents into SQLite staging for admin RAG review."""

    def __init__(self, download_dir: str | None = None) -> None:
        self.download_dir = Path(download_dir or settings.database_root) / "scraped"
        self.pdf_dir = self.download_dir / "pdf"
        self.img_dir = self.download_dir / "images"
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.img_dir.mkdir(parents=True, exist_ok=True)

    async def scrape_site(self, seed_url: str = "https://moald.gov.np", max_files: int = 10) -> dict[str, Any]:
        """Crawl seed site until it saves up to max_files target documents into SQLite staging."""
        logger.info(f"Starting government scraper for: {seed_url} (target count: {max_files})")
        results = {"pdfs": [], "images": [], "urls_visited": 0, "saved_to_sqlite": 0}

        async with httpx.AsyncClient(headers=HEADERS, verify=False, timeout=25.0, follow_redirects=True) as client:
            try:
                resp = await client.get(seed_url)
                if resp.status_code != 200:
                    return results

                scraper_db.mark_visited(seed_url)
                results["urls_visited"] += 1
                soup = BeautifulSoup(resp.text, "html.parser")

                for tag in soup.find_all(["a", "img"]):
                    if (len(results["pdfs"]) + len(results["images"])) >= max_files:
                        break

                    raw = tag.get("href") if tag.name == "a" else tag.get("src")
                    if not raw or raw.startswith(("mailto:", "javascript:", "tel:", "#")):
                        continue

                    try:
                        full_url = str(URL(seed_url).join(URL(raw)).with_fragment(None))
                        domain = URL(full_url).host
                        if not domain or not any(domain.endswith(ext) for ext in ALLOWED_DOMAINS):
                            continue

                        if scraper_db.is_visited_or_dead(full_url):
                            continue

                        # 1. Process PDF file
                        if full_url.lower().endswith(".pdf"):
                            path = await self._download_file(client, full_url, self.pdf_dir)
                            if path:
                                title = tag.get_text(strip=True) or path.name
                                doc = scraper_db.save_scraped_document(
                                    url=full_url,
                                    title=title[:100],
                                    file_type="pdf",
                                    file_path=str(path),
                                    file_size_bytes=path.stat().st_size,
                                    status="scraped",
                                    category="diseases",
                                )
                                results["pdfs"].append(doc)
                                results["saved_to_sqlite"] += 1
                                scraper_db.mark_visited(full_url)

                        # 2. Process Image file
                        elif full_url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                            path = await self._download_file(client, full_url, self.img_dir)
                            if path:
                                title = tag.get("alt") or tag.get("title") or path.name
                                doc = scraper_db.save_scraped_document(
                                    url=full_url,
                                    title=title[:100],
                                    file_type="image",
                                    file_path=str(path),
                                    file_size_bytes=path.stat().st_size,
                                    status="scraped",
                                    category="gallery",
                                )
                                results["images"].append(doc)
                                results["saved_to_sqlite"] += 1
                                scraper_db.mark_visited(full_url)

                    except Exception as e:
                        logger.debug(f"Error parsing URL {raw}: {e}")

            except Exception as e:
                logger.error(f"Error crawling {seed_url}: {e}")

        logger.info(
            f"Scrape completed for {seed_url}. Staged {results['saved_to_sqlite']} documents in SQLite (PDFs: {len(results['pdfs'])}, Images: {len(results['images'])})."
        )
        return results

    async def _download_file(self, client: httpx.AsyncClient, url: str, dest_folder: Path) -> Path | None:
        """Download file content and save locally."""
        try:
            resp = await client.get(url)
            if resp.status_code == 200 and len(resp.content) > 1024:
                raw_name = url.split("/")[-1].split("?")[0]
                clean = "".join([c for c in raw_name if c.isalnum() or c in (".", "_", "-")])
                if not clean or len(clean) > 50:
                    clean = hashlib.md5(url.encode()).hexdigest()[:12] + Path(url).suffix

                dest_path = dest_folder / clean
                dest_path.write_bytes(resp.content)
                return dest_path
        except Exception as e:
            logger.warning(f"Download error for {url}: {e}")
        return None


# Singleton instance
gov_scraper_service = GovAgricultureScraper()
