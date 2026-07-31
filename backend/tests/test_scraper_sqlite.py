"""
Automated unit test suite for SQLite Scraper Staging and Human-in-the-Loop Gemma 4 RAG Ingestion Pipeline.
"""

from fastapi.testclient import TestClient
from main import app
from db.scraper_db import scraper_db

client = TestClient(app)


import uuid

def test_sqlite_staging_document_flow():
    """Test saving a scraped document in SQLite, inspecting it, and gradually ingesting it."""
    url = f"https://moald.gov.np/test_document_{uuid.uuid4().hex[:8]}.pdf"
    title = "धान खेती प्रविधि तथा रोग नियन्त्रण निर्देशिका"

    # 1. Save document to SQLite staging
    doc = scraper_db.save_scraped_document(
        url=url,
        title=title,
        file_type="pdf",
        file_path="database/scraped/pdf/test_document.pdf",
        file_size_bytes=45000,
        status="scraped",
    )
    assert doc["status"] == "scraped"
    doc_id = doc["id"]

    # 2. List scraped documents from REST API
    list_res = client.get("/api/admin/rag/scraped?status=scraped")
    assert list_res.status_code == 200
    docs = list_res.json()["documents"]
    assert any(d["id"] == doc_id for d in docs)

    # 3. Test Gradual Ingestion
    ingest_payload = {
        "doc_id": doc_id,
        "title": title,
        "category": "practices",
        "converted_text": "धान खेती प्रविधि: समयमा बीउ राख्ने, सिँचाइको उचित प्रबन्ध गर्ने र ब्लास्ट रोग रोक्न विषादी प्रयोग गर्ने।",
    }
    ingest_res = client.post(f"/api/admin/rag/scraped/{doc_id}/ingest", json=ingest_payload)
    assert ingest_res.status_code == 200
    assert ingest_res.json()["status"] == "success"

    # 4. Verify SQLite status updated to 'ingested'
    updated_doc = scraper_db.get_document(doc_id)
    assert updated_doc["status"] == "ingested"
    assert updated_doc["category"] == "practices"
