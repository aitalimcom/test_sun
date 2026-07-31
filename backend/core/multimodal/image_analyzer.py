import logging
from typing import Any
from langchain_core.messages import HumanMessage, SystemMessage
from core.model_registry import get_llm

logger = logging.getLogger(__name__)


class ImageAnalysis:
    """Represents structured image analysis outcome."""

    def __init__(
        self,
        image_type: str,
        description: str,
        detected_entities: list[str],
        ocr_text: str = "",
        confidence: float = 1.0,
    ) -> None:
        self.image_type = image_type  # "disease" | "species" | "soil" | "ocr_document" | "general_vqa"
        self.description = description
        self.detected_entities = detected_entities
        self.ocr_text = ocr_text
        self.confidence = confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_type": self.image_type,
            "description": self.description,
            "detected_entities": self.detected_entities,
            "ocr_text": self.ocr_text,
            "confidence": self.confidence,
        }


class ImageAnalyzer:
    """Analyzes base64-encoded images to classify intent and extract agricultural features."""

    def __init__(self) -> None:
        # Load the vision model (preferring vision settings)
        self.llm = get_llm("vision")

    async def analyze(self, image_b64: str, user_text: str = "") -> ImageAnalysis:
        """Analyze the image using the configured vision model."""
        logger.info("Analyzing image using vision LLM...")
        
        system_prompt = (
            "You are an agricultural vision AI expert. Analyze the provided image in context of agriculture.\n"
            "Identify what the image displays (e.g., crop leaf with disease, plant species, soil, or document/label).\n"
            "Respond ONLY with a valid JSON document matching this schema:\n"
            "{\n"
            "  \"image_type\": \"disease\" | \"species\" | \"soil\" | \"ocr_document\" | \"general_vqa\",\n"
            "  \"description\": \"Detailed description of the image in Nepali language\",\n"
            "  \"detected_entities\": [\"list of crops, insects, weeds, or products detected\"],\n"
            "  \"ocr_text\": \"Any readable text on products, documents, or signs (if any)\",\n"
            "  \"confidence\": 0.0 to 1.0\n"
            "}"
        )
        
        # Ensure image is properly formatted (strip data url prefixes if present)
        clean_b64 = image_b64
        if "," in image_b64:
            clean_b64 = image_b64.split(",")[1]
            
        image_url_dict = {"url": f"data:image/jpeg;base64,{clean_b64}"}
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": f"Analyze this image. User question/text: {user_text}"},
                {"type": "image_url", "image_url": image_url_dict}
            ]
        )
        
        try:
            # We can invoke the LLM with system instruction or wrap it in message list
            messages = [
                SystemMessage(content=system_prompt),
                message
            ]
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            # Simple JSON parser
            parsed = self._parse_json(content)
            if parsed:
                return ImageAnalysis(
                    image_type=parsed.get("image_type", "general_vqa"),
                    description=parsed.get("description", "तस्विरको विश्लेषण उपलब्ध छैन।"),
                    detected_entities=parsed.get("detected_entities", []),
                    ocr_text=parsed.get("ocr_text", ""),
                    confidence=float(parsed.get("confidence", 0.8)),
                )
            
            # Fallback
            return ImageAnalysis(
                image_type="general_vqa",
                description=content,
                detected_entities=[],
                confidence=0.5
            )
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return ImageAnalysis(
                image_type="general_vqa",
                description="तस्विर विश्लेषण प्रक्रियामा त्रुटि भयो।",
                detected_entities=[],
                confidence=0.1
            )

    def _parse_json(self, text: str) -> dict | None:
        import json
        import re
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
        # Extract json markdown if present
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None
