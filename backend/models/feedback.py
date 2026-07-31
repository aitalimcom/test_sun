from pydantic import BaseModel
from typing import List, Optional


class FeedbackRequest(BaseModel):
    feedback_id: str
    session_id: str
    rating: int  # e.g., 1 to 5 or binary thumbs
    comment: Optional[str] = ""
    query: Optional[str] = ""
    response_text: Optional[str] = ""


class FeedbackResponse(BaseModel):
    success: bool
    message: str
    feedback_id: str
