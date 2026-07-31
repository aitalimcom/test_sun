import json
import logging
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage
from core.agent import BaseAgent
from core.state import AgentState

logger = logging.getLogger(__name__)

WRITER_SYSTEM_PROMPT = """You are KrishiMitra's Gemma-focused RAG Chunk Writer Agent.
Your job is to format raw text extracted from agricultural documents/PDFs/images into clean Markdown chunks.

Rules:
1. DO NOT translate English text into Nepali if the original is in English. Keep English as English.
2. If the text is in Nepali, keep it in Nepali, BUT add relevant technical English words in parentheses (e.g., "आलुको डढुवा (Late Blight / Phytophthora infestans)", "यूरिया मल (Urea fertilizer)") to enable cross-lingual keyword matching.
3. Structure output with markdown headings (#, ##), bullet points, and dosages.
4. Include source metadata block at the top.

Return ONLY a valid JSON object:
{
  "title_np": "Title in Nepali/English",
  "category": "diseases|practices|guides",
  "content": "Full formatted markdown content with English keywords in parentheses",
  "english_keywords": ["potato", "late blight", "phytophthora"]
}"""


class RAGWriterAgent(BaseAgent):
    """Gemma-focused bilingual writer agent that structures extracted text into RAG Markdown chunks."""

    name = "writer"
    description = "RAG लेखक एजेन्ट - कच्चा दस्तावेजबाट द्विभाषीय RAG ज्ञान चङ्क सिर्जना गर्ने कार्य"
    model_preference = "default"

    @property
    def system_prompt(self) -> str:
        return WRITER_SYSTEM_PROMPT

    async def generate_chunk(self, raw_text: str, doc_name: str = "Unknown") -> dict[str, Any]:
        """Generate structured RAG chunk from raw text."""
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Document Name: {doc_name}\nRaw Text:\n{raw_text[:2000]}")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()

            # Clean JSON markdown fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            parsed = json.loads(content)
            return {
                "title": parsed.get("title_np", doc_name),
                "category": parsed.get("category", "guides"),
                "content": parsed.get("content", raw_text),
                "english_keywords": parsed.get("english_keywords", []),
                "model_used": "gemma-4",
                "source": doc_name,
            }
        except Exception as e:
            logger.error(f"Writer agent chunk generation failed: {e}")
            return {
                "title": doc_name,
                "category": "guides",
                "content": raw_text,
                "english_keywords": [],
                "model_used": "gemma-4",
                "source": doc_name,
            }

    async def execute(self, state: AgentState) -> dict[str, Any]:
        raw_text = state.get("dispatch_query", "")
        chunk = await self.generate_chunk(raw_text)
        return {
            "result": chunk,
            "success": True,
        }
