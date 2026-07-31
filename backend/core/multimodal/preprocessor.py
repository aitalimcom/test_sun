import logging
from typing import Any
from core.multimodal.image_analyzer import ImageAnalyzer, ImageAnalysis
from core.multimodal.audio_processor import AudioProcessor
from core.multimodal.language_normalizer import LanguageNormalizer

logger = logging.getLogger(__name__)


class ProcessedInput:
    """Contains standardized input parameters after preprocessing."""

    def __init__(
        self,
        original_text: str,
        normalized_text: str,
        detected_language: str,
        image_analyses: list[ImageAnalysis],
        enriched_context: str,
    ) -> None:
        self.original_text = original_text
        self.normalized_text = normalized_text
        self.detected_language = detected_language
        self.image_analyses = image_analyses
        self.enriched_context = enriched_context

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "detected_language": self.detected_language,
            "image_analyses": [analysis.to_dict() for analysis in self.image_analyses],
            "enriched_context": self.enriched_context,
        }


class MultimodalPreprocessor:
    """Orchestrates audio transcription, image analysis, and query normalization."""

    def __init__(self) -> None:
        self.image_analyzer = ImageAnalyzer()
        self.audio_processor = AudioProcessor()
        self.language_normalizer = LanguageNormalizer()

    async def process(
        self,
        text: str | None,
        images: list[str] | None = None,
        audio_data: str | None = None,
        source_language: str = "auto",
    ) -> ProcessedInput:
        """Process multimodal inputs and consolidate them into a standard query context."""
        logger.info("Starting multimodal preprocessing...")
        
        raw_query = text or ""
        detected_lang = source_language
        
        # 1. Transcribe audio if present
        if audio_data:
            audio_res = await self.audio_processor.transcribe(audio_data)
            raw_query = audio_res.raw_text
            detected_lang = audio_res.detected_language
            
        # 2. Normalize text script and language to Devanagari Nepali
        normalized_query = ""
        if raw_query:
            normalized_query = await self.language_normalizer.normalize(raw_query, source_lang=detected_lang)
            
        # 3. Analyze images if present
        image_analyses = []
        image_contexts = []
        
        if images:
            for i, img_b64 in enumerate(images):
                analysis = await self.image_analyzer.analyze(img_b64, user_text=raw_query)
                image_analyses.append(analysis)
                
                # Formulate a text representation of what the model sees in the image
                desc = f"[तस्विर {i+1} विश्लेषण - प्रकार: {analysis.image_type}, विवरण: {analysis.description}]"
                image_contexts.append(desc)
                
        # 4. Formulate enriched context (combination of text query + image insights)
        enriched_context_list = []
        if normalized_query:
            enriched_context_list.append(normalized_query)
        if image_contexts:
            enriched_context_list.extend(image_contexts)
            
        enriched_context = " ".join(enriched_context_list)
        
        # If the user only uploaded an image without query text, use the image description as query
        if not normalized_query and image_analyses:
            normalized_query = f"तस्विरमा देखिएको बाली/समस्याको पहिचान र उपचार के हो? ({image_analyses[0].description})"
            if not enriched_context:
                enriched_context = normalized_query
                
        logger.info("Multimodal preprocessing complete.")
        return ProcessedInput(
            original_text=text or "",
            normalized_text=normalized_query,
            detected_language=detected_lang,
            image_analyses=image_analyses,
            enriched_context=enriched_context,
        )
class_name = "MultimodalPreprocessor"
