"""
Admin RAG & Government Scraper Management API Router.
Handles SQLite staging document inspection with Gemma 4 AI, Preeti font conversion,
and gradual human-in-the-loop ingestion into ChromaDB / BM25 Knowledge & Gallery databases.
"""

from __future__ import annotations

import logging
import uuid
import base64
import pypdf
import io
import json
import re
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from config import settings
from db.scraper_db import scraper_db
from db.source import source_db
from db.knowledge import knowledge_db
from db.gallery import gallery_db
from core.preeti import is_preeti_text, preeti_to_unicode
from services.rag.hybrid_retriever import hybrid_retriever
from services.search.gov_scraper import gov_scraper_service
from agents.writer.agent import RAGWriterAgent
from core.multimodal.image_analyzer import ImageAnalyzer
from core.model_registry import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/rag", tags=["Admin RAG Management"])


class InspectResponse(BaseModel):
    doc_id: str
    filename: str
    file_type: str
    page_count: int
    is_image: bool
    is_preeti: bool
    is_agriculture: bool
    relevance_reason: str
    preview_text_raw: str
    preview_text_converted: str
    recommended_category: str = "diseases"


class IngestRequest(BaseModel):
    doc_id: str
    title: str
    category: str = "diseases"  # diseases | practices | guides | gallery
    converted_text: str
    is_gallery_image: bool = False
    crop_type: str = "potato"


class ScrapeRequest(BaseModel):
    url: str = "https://moald.gov.np"
    max_files: int = 10


# ─────────────────────────────────────────────────────────────
# 1. SQLITE STAGING SCRAPED DOCUMENT ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.get("/scraped")
async def list_scraped_documents(status: str | None = None, limit: int = 100):
    """List documents stored in SQLite staging database."""
    docs = scraper_db.list_scraped_documents(status=status, limit=limit)
    return {"documents": docs, "count": len(docs)}


@router.get("/scraped/{doc_id}")
async def get_scraped_document(doc_id: str):
    """Get single document record from SQLite staging."""
    doc = scraper_db.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found in SQLite staging.")
    return {"document": doc}


@router.post("/scraped/{doc_id}/inspect", response_model=InspectResponse)
async def inspect_scraped_document(doc_id: str):
    """Run Gemma 4 text extraction / Vision OCR, Preeti font conversion, and agri relevance check on a staged document."""
    doc = scraper_db.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    file_path = Path(doc["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found on disk: {doc['file_path']}")

    filename = file_path.name
    file_bytes = file_path.read_bytes()

    raw_combined = ""
    converted_text = ""
    is_preeti = False
    is_image = False
    page_count = 1
    file_type = doc.get("file_type", "pdf")

    # CASE A: IMAGE DOCUMENTS (Vision OCR)
    if file_type == "image" or filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        is_image = True
        logger.info(f"Inspecting image {filename} with Gemma 4 Vision OCR...")
        b64_img = base64.b64encode(file_bytes).decode("utf-8")
        analyzer = ImageAnalyzer()
        ocr_res_obj = await analyzer.analyze(
            b64_img,
            user_text="Extract all agricultural text, disease captions, crop names, and symptoms in Nepali/English."
        )
        raw_combined = ocr_res_obj.ocr_text or ocr_res_obj.description or f"तस्विर OCR ({filename})"
        converted_text = raw_combined

    # CASE B: PDF DOCUMENTS
    elif file_type == "pdf" or filename.lower().endswith(".pdf"):
        try:
            pdf_file = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(pdf_file)
            page_count = len(reader.pages)
            raw_pages = []
            for i in range(min(3, page_count)):
                raw_pages.append(reader.pages[i].extract_text() or "")
            raw_combined = "\n\n".join(raw_pages).strip()

            if raw_combined and is_preeti_text(raw_combined):
                is_preeti = True
                converted_text = preeti_to_unicode(raw_combined)
            else:
                converted_text = raw_combined

            if not raw_combined:
                raw_combined = f"स्क्यान गरिएको PDF: {filename} (Gemma Vision OCR प्रयोग गरिनेछ)"
                converted_text = raw_combined
        except Exception as e:
            logger.warning(f"PDF extraction error for {filename}: {e}")
            raw_combined = f"PDF extraction fallback for {filename}"
            converted_text = raw_combined
    else:
        raw_combined = file_bytes.decode("utf-8", errors="ignore")
        converted_text = raw_combined

    # Gemma 4 Agriculture Relevance & Category Evaluation
    is_agri, reason, category = await _evaluate_with_gemma(converted_text, is_image=is_image)

    # Save inspection state into SQLite staging
    scraper_db.update_document_inspection(
        doc_id=doc_id,
        raw_text=raw_combined,
        converted_text=converted_text,
        is_preeti=is_preeti,
        is_agriculture=is_agri,
        relevance_reason=reason,
        summary=converted_text[:200],
        category=category,
    )

    return InspectResponse(
        doc_id=doc_id,
        filename=filename,
        file_type=file_type,
        page_count=page_count,
        is_image=is_image,
        is_preeti=is_preeti,
        is_agriculture=is_agri,
        relevance_reason=reason,
        preview_text_raw=raw_combined[:1000],
        preview_text_converted=converted_text[:1000],
        recommended_category=category,
    )


@router.post("/scraped/{doc_id}/ingest")
async def ingest_scraped_document(doc_id: str, req: IngestRequest | None = None):
    """Approve and gradually ingest a inspected document from SQLite staging into RAG Knowledge Base or Gallery DB."""
    doc = scraper_db.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found in SQLite staging.")

    title = req.title if req else doc.get("title") or doc["id"]
    category = req.category if req else doc.get("category") or "diseases"
    converted_text = (req.converted_text if req and req.converted_text else doc.get("converted_text")) or doc.get("raw_text") or "कृषि जानकारी"

    # Save source
    source_db.save_source(doc_id, converted_text, {"title": title, "category": category, "url": doc.get("url")})

    if category == "gallery" or (req and req.is_gallery_image) or doc.get("file_type") == "image":
        item = gallery_db.add_item(
            image_path=doc.get("file_path", f"scraped/{doc_id}.jpg"),
            caption_np=title,
            crop_type=req.crop_type if req else "potato",
            disease_tags=["कृषि तस्विर", "बाली स्वास्थ्य"],
            visual_features=converted_text[:200],
        )
        scraper_db.mark_ingested(doc_id, category="gallery")
        return {
            "status": "success",
            "doc_id": doc_id,
            "type": "gallery",
            "message": f"तस्विर '{title}' सफलता पूर्वक ग्यालरी कोषमा थपियो।"
        }

    # Generate Markdown Chunk for RAG
    writer = RAGWriterAgent()
    chunk = await writer.generate_chunk(converted_text, doc_name=title)

    cat_dir = Path(settings.database_root) / "knowledge" / category
    cat_dir.mkdir(parents=True, exist_ok=True)
    chunk_file = cat_dir / f"{doc_id}.md"
    chunk_file.write_text(chunk.get("content", converted_text), encoding="utf-8")

    # Update SQLite Status
    scraper_db.mark_ingested(doc_id, category=category)

    # Re-index Hybrid Retriever
    all_docs = knowledge_db.list_documents()
    corpus = []
    for d in all_docs:
        c = knowledge_db.get_document(d["category"], d["id"])
        if c:
            corpus.append({"content": c, "source": d["filename"], "title": d["id"], "category": d["category"]})
    hybrid_retriever.index_corpus(corpus)

    return {
        "status": "success",
        "doc_id": doc_id,
        "category": category,
        "message": f"दस्तावेज '{title}' सफलता पूर्वक RAG ज्ञान कोषमा इन्जेस्ट गरियो।"
    }


@router.post("/scraped/{doc_id}/reject")
async def reject_scraped_document(doc_id: str, reason: str = "प्रसासक द्वारा अस्वीकृत"):
    """Mark a scraped document as rejected."""
    success = scraper_db.mark_rejected(doc_id, reason=reason)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"status": "success", "message": f"Document {doc_id} marked as rejected."}


# ─────────────────────────────────────────────────────────────
# 2. FILE UPLOAD INSPECTION & TRIGGER SCRAPE
# ─────────────────────────────────────────────────────────────

@router.post("/inspect", response_model=InspectResponse)
async def inspect_uploaded_document(file: UploadFile = File(...)) -> Any:
    """Inspect uploaded PDF/Image file."""
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    filename = file.filename or "uploaded.pdf"
    file_bytes = await file.read()

    file_type = "pdf" if filename.lower().endswith(".pdf") else "image"
    temp_dir = Path(settings.database_root) / "scraped" / file_type
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / f"{doc_id}_{filename}"
    temp_path.write_bytes(file_bytes)

    # Save to SQLite staging
    staged = scraper_db.save_scraped_document(
        url=f"upload://{doc_id}/{filename}",
        title=filename,
        file_type=file_type,
        file_path=str(temp_path),
        file_size_bytes=len(file_bytes),
        status="scraped",
    )

    return await inspect_scraped_document(staged["id"])


@router.post("/scrape")
async def trigger_gov_scrape(req: ScrapeRequest) -> Any:
    """Scrape government agricultural site for N files into SQLite staging."""
    try:
        results = await gov_scraper_service.scrape_site(req.url, max_files=req.max_files)
        total_staged = results.get("saved_to_sqlite", 0)
        return {
            "status": "success",
            "seed_url": req.url,
            "results": results,
            "message": f"सफलतापूर्वक {total_staged} वटा दस्तावेजहरू (PDFs/Images) SQLite database मा प्राप्त भयो।",
        }
    except Exception as e:
        logger.error(f"Gov scraper error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents() -> Any:
    """List ingested knowledge chunks and sources."""
    sources = source_db.list_sources()
    knowledge_docs = knowledge_db.list_documents()
    return {"sources": sources, "knowledge_docs": knowledge_docs}


@router.get("/gallery")
async def list_gallery(crop: str | None = "potato") -> Any:
    """List visual gallery items."""
    return {"gallery": gallery_db.list_gallery(crop_type=crop)}


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

async def _evaluate_with_gemma(text: str, is_image: bool = False) -> tuple[bool, str, str]:
    """Helper using Gemma 4 to classify agri relevance and recommend category."""
    if not text or len(text.strip()) < 5:
        return True, "सामग्री उपलब्ध छ", "gallery" if is_image else "guides"

    agri_keywords = ["कृषि", "बाली", "मल", "रोग", "धान", "मकै", "आलु", "गहुँ", "agriculture", "crop", "pesticide", "seed", "farm"]
    if any(kw in text.lower() for kw in agri_keywords):
        cat = "gallery" if is_image else ("diseases" if "रोग" in text or "कीरा" in text else "practices")
        return True, "कृषि शब्दहरू समावेश छन्", cat

    prompt = (
        "Analyze this document snippet and determine if it is related to agriculture.\n"
        "Respond ONLY with valid JSON: {\"is_agriculture\": true/false, \"reason\": \"explanation in Nepali\", \"category\": \"diseases\"|\"practices\"|\"guides\"|\"gallery\"}"
    )

    try:
        llm = get_llm("routing")
        messages = [SystemMessage(content=prompt), HumanMessage(content=text[:1500])]
        resp = await llm.ainvoke(messages)
        match = re.search(r"\{[\s\S]*\}", resp.content.strip())
        if match:
            parsed = json.loads(match.group(0))
            return parsed.get("is_agriculture", True), parsed.get("reason", "कृषि विषयवस्तु"), parsed.get("category", "diseases")
    except Exception as e:
        logger.warning(f"Gemma evaluation warning: {e}")

    return True, "कृषि सम्बन्धी दस्तावेज", "diseases"
