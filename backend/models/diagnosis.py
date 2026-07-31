from pydantic import BaseModel
from typing import List, Optional


class DiagnoseRequest(BaseModel):
    image: str                       # base64 encoded
    crop_type: Optional[str] = "अन्य"
    description: Optional[str] = ""


class DiagnoseResponse(BaseModel):
    diagnosis_id: str
    crop_type: str
    result: dict                     # Structured diagnosis output dict
    created_at: str
