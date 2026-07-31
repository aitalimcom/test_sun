"""
Admin Feedback & Conversation Audit API Router.
Enables experts to review reported chats, record model corrections, and export alignment datasets.
"""

from __future__ import annotations

import logging
from typing import Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from db.feedback import feedback_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/feedback", tags=["Admin Feedback Audits"])


class CorrectionRequest(BaseModel):
    expert_correction: str


@router.get("/reported")
async def list_reported_chats(limit: int = 100):
    """List conversations reported by farmers with bad feedback."""
    reports = feedback_db.list_reported_chats(limit=limit)
    return {"reported_chats": reports, "count": len(reports)}


@router.post("/reported/{record_id}/correction")
async def add_expert_correction(record_id: str, payload: CorrectionRequest):
    """Add expert correction to a reported conversation for Gemma alignment."""
    updated = feedback_db.update_expert_correction(record_id, payload.expert_correction)
    if not updated:
        raise HTTPException(status_code=404, detail="Reported conversation not found.")
    return {"status": "success", "record": updated}


@router.get("/export")
async def export_alignment_dataset():
    """Export reported conversations as JSONL for Gemma model training / fine-tuning."""
    dataset = feedback_db.export_for_alignment()
    return JSONResponse(
        content=dataset,
        headers={"Content-Disposition": "attachment; filename=gemma_alignment_dataset.json"}
    )
