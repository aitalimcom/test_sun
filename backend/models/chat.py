from pydantic import BaseModel
from typing import Any, List, Optional


class ChatRequest(BaseModel):
    message: str = ""
    session_id: Optional[str] = None
    images: List[str] = []           # base64 encoded strings
    audio_data: Optional[str] = None # base64 encoded audio
    language: str = "auto"


class TaskItem(BaseModel):
    title: str
    description: str
    due_date: Optional[str] = None


class AlertItem(BaseModel):
    title: str
    severity: str  # info | warning | danger
    description: str


class ReportItem(BaseModel):
    title: str
    summary: str
    data: dict[str, Any]


class ChatResponse(BaseModel):
    response: str                    # Main Nepali reply text
    output_type: str                 # chat | task | alert | report
    tasks: Optional[List[TaskItem]] = None
    alerts: Optional[List[AlertItem]] = None
    report: Optional[ReportItem] = None
    agent_trace: List[dict] = []
    suggestions: List[str] = []
    feedback_id: str                 # Audit tracker ID
    session_id: str
