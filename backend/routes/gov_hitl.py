"""
Government Human-in-the-Loop (HITL) & Alignment Router.
REST API for Ministry of Agriculture JTAs to audit AI responses and export Gemma 4 DPO datasets.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from core.hitl import gov_hitl_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/gov/hitl", tags=["Government HITL Alignment"])


class VerificationRequest(BaseModel):
    jta_corrected_response: str
    jta_officer_id: str = "JTA-OFFICER-001"
    error_tags: List[str] = []
    approve_raw: bool = False


class SubmitReviewRequest(BaseModel):
    user_query: str
    gemma_raw_response: str
    district: str = "काठमाडौँ"
    crop: str = "सामान्य"
    reformulated_query: Optional[str] = None
    dialect: str = "Standard Nepali"


@router.get("/pending")
async def list_pending_audits(limit: int = 50):
    """List pending AI responses requiring Government JTA review."""
    pending = gov_hitl_engine.list_pending(limit=limit)
    return {"pending_audits": pending, "count": len(pending)}


@router.post("/submit")
async def submit_chat_for_review(payload: SubmitReviewRequest):
    """Enqueues a raw chat response for JTA review."""
    record_id = gov_hitl_engine.submit_for_review(
        user_query=payload.user_query,
        gemma_raw_response=payload.gemma_raw_response,
        district=payload.district,
        crop=payload.crop,
        reformulated_query=payload.reformulated_query,
        dialect=payload.dialect
    )
    return {"status": "success", "record_id": record_id}


@router.post("/verify/{record_id}")
async def submit_jta_verification(record_id: str, payload: VerificationRequest):
    """Submits JTA expert review, agronomic corrections, and error tagging."""
    success = gov_hitl_engine.verify_record(
        record_id=record_id,
        jta_corrected_response=payload.jta_corrected_response,
        jta_officer_id=payload.jta_officer_id,
        error_tags=payload.error_tags,
        approve_raw=payload.approve_raw
    )
    if not success:
        raise HTTPException(status_code=404, detail="HITL audit record not found.")

    return {"status": "success", "record_id": record_id, "verified": True}


@router.get("/export/dpo")
async def export_dpo_alignment_dataset():
    """Exports verified records as DPO (Direct Preference Optimization) JSONL for Gemma 4 fine-tuning."""
    dataset = gov_hitl_engine.export_dpo_jsonl()
    import json
    jsonl_output = "\n".join(json.dumps(item, ensure_ascii=False) for item in dataset)

    return Response(
        content=jsonl_output,
        media_type="application/x-jsonlines",
        headers={"Content-Disposition": "attachment; filename=gemma4_nepali_dpo_alignment.jsonl"}
    )


@router.get("/stats")
async def get_hitl_statistics():
    """Returns HITL verification stats, error tag frequencies, and accuracy metrics."""
    stats = gov_hitl_engine.get_stats()
    return stats
