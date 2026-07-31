from pydantic import BaseModel
from typing import Any, List, Optional


class StatusResponse(BaseModel):
    status: str
    message: str


class AuditTrace(BaseModel):
    agent_name: str
    success: bool
    error: Optional[str] = None
