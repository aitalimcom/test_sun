import logging
from langchain_core.messages import SystemMessage, HumanMessage
from core.model_registry import get_llm

logger = logging.getLogger(__name__)


class LanguageNormalizer:
    """Standardizes input queries from different languages and scripts into clean Devanagari Nepali."""

    def __init__(self) -> None:
        self.llm = get_llm("routing")  # Use a lighter model for quick translation/normalization

    async def normalize(self, text: str, source_lang: str = "auto") -> str:
        """Translate or transliterate user query into standard Devanagari Nepali.

        Handles:
        - Romanized Nepali (e.g., "malami roga lagyo" -> "मलमी रोग लाग्यो")
        - English queries (e.g., "How to grow potatoes?" -> "आलु कसरी रोप्ने?")
        - Hindi/mixed queries.
        """
        if not text or not text.strip():
            return ""

        # Quick check: if the text is already purely Devanagari Nepali, we might bypass LLM for speed,
        # but running it through normalization ensures spelling correction and standardized phrasing.
        logger.info(f"Normalizing language for query: '{text[:50]}'")

        system_prompt = (
            "You are a language standardization assistant for Nepali farmers.\n"
            "Your task is to translate, transliterate, and normalize the user's input query into standardized, "
            "clear Devanagari Nepali script. Correct any spelling errors, romanized script, or slang.\n"
            "Keep technical terms (like NPK, pH, or scientific names) in Devanagari or standard form in parentheses if helpful.\n"
            "Respond ONLY with the normalized Devanagari Nepali text, and nothing else. No explanations, no introduction."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Normalize this query: {text}")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            normalized = response.content.strip()
            
            # Simple clean up (removing quotes/prefixes if LLM hallucinates them)
            normalized = normalized.replace('"', '').replace("'", "")
            logger.info(f"Normalized query output: '{normalized}'")
            return normalized
        except Exception as e:
            logger.error(f"Language normalization failed: {e}")
            return text  # Fallback to original text if translation fails
