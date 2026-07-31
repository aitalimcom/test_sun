from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.ocr import analyze_document, extract_fields, detect_face

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


class ImageRequest(BaseModel):
    image: str


class DocumentInfo(BaseModel):
    document_type: str | None = None
    document_type_np: str | None = None
    is_readable: bool = False
    confidence: str = "low"
    detected_text_summary: str | None = None
    has_face_photo: bool = False
    face_location: str | None = None


class FieldSuggestion(BaseModel):
    value: str | None = None
    confidence: str = "low"


class ExtractedFields(BaseModel):
    first_name: FieldSuggestion | None = None
    last_name: FieldSuggestion | None = None
    citizenship_number: FieldSuggestion | None = None
    gender: FieldSuggestion | None = None
    date_of_birth: FieldSuggestion | None = None
    father_name: FieldSuggestion | None = None
    mother_name: FieldSuggestion | None = None
    address: FieldSuggestion | None = None


class FaceInfo(BaseModel):
    face_found: bool = False
    face_description: str | None = None
    face_region: dict | None = None
    estimated_age: str | None = None
    gender_appearance: str | None = None


class FullOCRResult(BaseModel):
    document: DocumentInfo
    fields: ExtractedFields
    face: FaceInfo


@router.post("/analyze", response_model=DocumentInfo)
async def ocr_analyze(req: ImageRequest):
    """Step 1: Detect document type."""
    try:
        data = await analyze_document(req.image)
        return DocumentInfo(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract", response_model=ExtractedFields)
async def ocr_extract(req: ImageRequest):
    """Step 2: Extract fields with confidence."""
    try:
        data = await extract_fields(req.image)
        return ExtractedFields(**{k: FieldSuggestion(**v) if isinstance(v, dict) else v for k, v in data.items()})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/face", response_model=FaceInfo)
async def ocr_face(req: ImageRequest):
    """Step 3: Detect face in document."""
    try:
        data = await detect_face(req.image)
        return FaceInfo(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/full", response_model=FullOCRResult)
async def ocr_full(req: ImageRequest):
    """Run all 3 steps: analyze + extract + face detection."""
    try:
        doc_info = await analyze_document(req.image)
        fields_raw = await extract_fields(req.image)
        face_info = await detect_face(req.image)

        fields = ExtractedFields(**{
            k: FieldSuggestion(**v) if isinstance(v, dict) else v
            for k, v in fields_raw.items()
        })

        return FullOCRResult(
            document=DocumentInfo(**doc_info),
            fields=fields,
            face=FaceInfo(**face_info),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
