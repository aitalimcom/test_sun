"""
Gemma 4 Query Reformulation Agent.
Engineered specifically for the Gemma Nepali Language Accessibility Challenge:
- Transliterates Romanized Nepali to standard Devanagari (e.g. 'dadhuwa' -> 'डढुवा', 'bajar' -> 'बजार')
- Resolves ambiguous conjuncts (e.g. क्ष, त्र, ज्ञ, द्ध, ष्ट)
- Normalizes Hraswa/Dirga spelling variations (e.g. आलु vs आलू)
- Resolves code-switching (mixing English & Nepali in same query)
- Expands query into 3 search variations for high-recall RAG retrieval.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from langchain_core.messages import SystemMessage, HumanMessage

from core.agent import BaseAgent
from core.state import AgentState
from core.normalizer import normalize_nepali_text

logger = logging.getLogger(__name__)

GEMMA_ACCESSIBILITY_REFORMULATOR_PROMPT = """You are Gemma 4's Specialized Nepali Language & Devanagari Transliteration Reformulator for Krishi Sewa.

YOUR CORE MISSION (Gemma Nepali Language Accessibility):
1. **Romanized Transliteration**: If the user inputs Romanized Nepali (e.g. "aaloo ma dadhuwa rog lagyo", "bajar bhau kati chha"), convert it to correct Devanagari script ("आलुमा डढुवा रोग लाग्यो", "कालिमाटी बजार भाउ").
2. **Ambiguous Conjuncts & Phonetic Normalization**: Resolve Devanagari conjunct ambiguities (e.g. क्ष/छ, त्र/तर, ज्ञ/ग्य, द्ध/ध) and Hraswa/Dirga spelling variations (e.g. आलु/आलू, सिँचाइ/सिचाई).
3. **Code-Switching Resolution**: Handle mixed English and Nepali phrases (e.g. "tomato ma late blight ko spray bhandinus" -> "टमाटरको डढुवा रोगमा म्याङ्कोजेब विषादी प्रयोग").
4. **Regional Dialect Normalization**: Convert Terai/Hill regional dialect terms to standard agricultural Nepali.

OUTPUT FORMAT — Respond ONLY with a valid JSON document:
{
  "devanagari_standard": "प्रमाणित देवनागरी प्रश्न",
  "romanized_transliteration": "रोमनबाट देवनागरी रूपान्तरण",
  "queries": [
    "खोज प्रश्न १ (मानक देवनागरी)",
    "खोज प्रश्न २ (अंग्रेजी प्राविधिक / वैज्ञानिक नाम)",
    "खोज प्रश्न ३ (स्थानीय पर्यायवाची शब्द)"
  ]
}"""


class QueryReformulatorAgent(BaseAgent):
    """Expands farmer query into multiple search variations resolving Nepali script & phonetic edge cases."""

    name = "query_reformulator"
    description = "नेपाली भाषा तथा देवनागरी प्रश्न रूपान्तरण एजेन्ट"
    model_preference = "routing"

    @property
    def system_prompt(self) -> str:
        return GEMMA_ACCESSIBILITY_REFORMULATOR_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Gemma 4 Nepali Accessibility Query Reformulator...")
        query = state.get("normalized_query") or state.get("query") or ""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Reformulate and normalize this farmer query: {query}")
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            
            queries = [query, normalize_nepali_text(query)]
            try:
                parsed = json.loads(content)
                if "devanagari_standard" in parsed:
                    queries.insert(0, parsed["devanagari_standard"])
                if "queries" in parsed and isinstance(parsed["queries"], list):
                    queries.extend(parsed["queries"])
            except json.JSONDecodeError:
                pass
                
            unique_queries = list(dict.fromkeys(queries))
            logger.info(f"Gemma 4 generated multi-queries: {unique_queries}")
            
            return {
                "result": unique_queries,
                "success": True,
            }
        except Exception as e:
            logger.error(f"Query reformulator failed: {e}")
            return {
                "result": [query, normalize_nepali_text(query)],
                "success": False,
                "error": str(e)
            }

    async def reformulate(self, query: str) -> dict[str, Any]:
        """Convenience method for multi-query reformulation."""
        res = await self.execute({"normalized_query": query, "query": query})
        variations = res.get("result", [query])
        return {"variations": variations}
