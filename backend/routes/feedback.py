import logging
from fastapi import APIRouter, HTTPException
from typing import Any

from db.feedback import feedback_db
from models.feedback import FeedbackRequest, FeedbackResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["Audit Feedback"])


@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest) -> Any:
    """Submit farmer audit feedback on agent responses."""
    try:
        feedback_db.submit_feedback(
            feedback_id=request.feedback_id,
            session_id=request.session_id,
            rating=request.rating,
            comment=request.comment or "",
            query=request.query or "",
            response_text=request.response_text or "",
        )
        return FeedbackResponse(
            success=True,
            message="फिडब्याक सफलतापूर्वक दर्ता भयो। धन्यवाद!",
            feedback_id=request.feedback_id
        )
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
