import logging
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from services.rag.hybrid_retriever import hybrid_retriever
from services.search.web_search import web_search_service
from prompts.templates.disease import DISEASE_SYSTEM_PROMPT, DISEASE_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

POTATO_DISEASE_PROMPT_OVERRIDE = """You are KrishiMitra's Specialized Potato Crop Doctor (आलु रोग विशेषज्ञ).
Your primary target is identifying Potato (आलु) diseases and pests:
- Late Blight (आलुको डढुवा - Phytophthora infestans)
- Early Blight (आलुको अगेनी डढुवा - Alternaria solani)
- Potato Tuber Moth (आलुको पुतली/कीरा)
- Bacterial Wilt (जिवाणुजन्य ओइलाउने रोग)
- Common Scab & Black Scurf

Provide structured advice in Nepali:
1. Disease Name (रोगको नाम - English & Nepali)
2. Symptoms (प्रमुख लक्षणहरू)
3. Biological & Chemical Control (जैविक तथा रासायनिक रोकथामका उपाय)
4. Spray Window & Dosage (औषधी छर्ने मात्रा तथा तरिका)
"""


class DiseaseAgent(BaseAgent):
    """Diagnoses crop diseases with specialized Potato (आलु) profiling and web search fallback."""

    name = "disease"
    description = "बाली रोग विशेषज्ञ - आलु तथा अन्य बालीमा लाग्ने रोग पहिचान र उपचार"
    model_preference = "vision"

    @property
    def system_prompt(self) -> str:
        return POTATO_DISEASE_PROMPT_OVERRIDE

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Specialized Potato Disease agent...")
        dispatch_query = state.get("dispatch_query") or state.get("normalized_query") or state.get("query") or "तस्विर विश्लेषण गर्नुहोस्"
        
        # 1. Perform Hybrid RAG Search (BM25 + Vector)
        rag_results = []
        try:
            rag_results = await hybrid_retriever.retrieve(dispatch_query, limit=3)
        except Exception as e:
            logger.warning(f"Hybrid RAG retrieval failed in Disease agent: {e}")

        # 2. Web search fallback if query needs real-time disease treatment updates
        web_context = ""
        if not rag_results or "उपचार" in dispatch_query or "आलु" in dispatch_query:
            try:
                search_res = await web_search_service.search(f"potato disease Nepal treatment {dispatch_query}", max_results=2)
                web_context = str(search_res)
            except Exception as e:
                logger.warning(f"Web search fallback failed: {e}")

        analyses = state.get("image_analyses", [])
        rag_text = "\n".join([f"- {r.get('content', '')}" for r in rag_results])
        
        user_prompt = (
            f"रोग विवरण / प्रश्न: {dispatch_query}\n"
            f"तस्विर विश्लेषण (Image VQA): {analyses}\n"
            f"RAG ज्ञान कोष (Local Knowledge): {rag_text}\n"
            f"वेब नतिजा (Web Search Fallback): {web_context}\n\n"
            f"कृपा गरी किसानलाई आलु/बाली रोगको विस्तृत र प्रभावकारी उपचार सुझाव दिनुहोस्।"
        )

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            return {
                "result": content,
                "success": True,
                "new_messages": [{"role": "assistant", "content": content}],
                "rag_citations": [r.get("source", "Knowledge Base") for r in rag_results]
            }
        except Exception as e:
            logger.error(f"Disease agent execution failed: {e}")
            return {
                "result": "आलु रोग निदान प्रक्रियामा प्राविधिक त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
