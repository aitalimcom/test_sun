import httpx
import json
import base64
from config import settings


ANALYZE_PROMPT = """You are a document analysis AI. Look at this image carefully and determine:

1. What type of document is this? (citizenship card, passport, license, other)
2. Is the image clear enough to read text?
3. What text fields can you identify?

Return ONLY a valid JSON object:
{
  "document_type": "citizenship|passport|license|other",
  "document_type_np": "नागरिकता पत्र|पासपोर्ट|सवारी साधन अनुमति पत्र|अन्य",
  "is_readable": true,
  "confidence": "high|medium|low",
  "detected_text_summary": "brief summary of what text is visible",
  "has_face_photo": true,
  "face_location": "top-left|top-right|bottom-left|bottom-right|center"
}"""


EXTRACT_PROMPT = """You are a careful document reader. This image is a Nepali citizenship card (नागरिकता पत्र).

Look at the image and extract what you can SEE. Do NOT guess or infer anything.

For each field, provide:
- The value you actually read from the document
- A confidence level (high/medium/low) based on how clearly you can read it

Return ONLY a valid JSON object:
{
  "first_name": {"value": "...", "confidence": "high|medium|low"},
  "last_name": {"value": "...", "confidence": "high|medium|low"},
  "citizenship_number": {"value": "...", "confidence": "high|medium|low"},
  "gender": {"value": "पुरुष or महिला", "confidence": "high|medium|low"},
  "date_of_birth": {"value": "YYYY-MM-DD or null", "confidence": "high|medium|low"},
  "father_name": {"value": "... or null", "confidence": "high|medium|low"},
  "mother_name": {"value": "... or null", "confidence": "high|medium|low"},
  "address": {"value": "... or null", "confidence": "high|medium|low"}
}

Rules:
- Only return what you can ACTUALLY READ in the image
- If text is blurry, partial, or uncertain, set confidence to "low"
- If you cannot read a field at all, set value to null and confidence to "low"
- Preserve exact Devanagari spelling as printed on the document"""


FACE_PROMPT = """You are a face detection AI. Look at this document image and find the person's face/photo.

Return ONLY a valid JSON object:
{
  "face_found": true,
  "face_description": "brief description of the person in the photo",
  "face_region": {
    "x_percent": 10,
    "y_percent": 15,
    "width_percent": 25,
    "height_percent": 35
  },
  "estimated_age": "25-30",
  "gender_appearance": "पुरुष|महिला"
}

Rules:
- x_percent, y_percent = top-left corner position as percentage of image dimensions
- width_percent, height_percent = size as percentage of image dimensions
- If no face is found, set face_found to false and other fields to null"""


async def _call_gemma(image_b64: str, prompt: str, max_tokens: int = 512) -> dict:
    """Single Gemma 4 vision call via OpenRouter."""
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY not configured")

    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "temperature": 0.1,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    return json.loads(content)


def _clean_b64(image: str) -> str:
    if image.startswith("data:"):
        return image.split(",", 1)[1]
    return image


async def analyze_document(base64_image: str) -> dict:
    """Step 1: Detect what document type this is."""
    return await _call_gemma(_clean_b64(base64_image), ANALYZE_PROMPT, max_tokens=256)


async def extract_fields(base64_image: str) -> dict:
    """Step 2: Extract citizenship fields with confidence scores."""
    return await _call_gemma(_clean_b64(base64_image), EXTRACT_PROMPT, max_tokens=512)


async def detect_face(base64_image: str) -> dict:
    """Step 3: Find and describe the face in the document."""
    return await _call_gemma(_clean_b64(base64_image), FACE_PROMPT, max_tokens=256)
