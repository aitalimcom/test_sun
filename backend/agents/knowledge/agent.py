import logging
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.knowledge import KNOWLEDGE_SYSTEM_PROMPT, KNOWLEDGE_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class KnowledgeAgent(BaseAgent):
    """Answers agricultural queries by performing RAG search on the local wiki files."""

    name = "knowledge"
    description = "ज्ञान कोष खोज - स्थानीय निर्देशिका र कृषि निर्देशिका पुस्तकहरूबाट वैज्ञानिक तथ्यहरूको खोज"
    model_preference = "default"

    @property
    def system_prompt(self) -> str:
        return KNOWLEDGE_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Knowledge/RAG agent...")
        dispatch_query = state.get("dispatch_query", "")

        context = "स्थानीय कृषि विश्वकोशबाट सान्दर्भिक सामग्री फेला परेन।"

        # Perform RAG retrieval
        try:
            from services.rag.retriever import rag_retriever
            results = await rag_retriever.retrieve(dispatch_query, limit=3)
            if results:
                context = "\n\n".join([f"[{i+1}] स्रोत: {doc.get('source', 'अज्ञात')}\n{doc.get('content', '')}" for i, doc in enumerate(results)])
        except Exception as e:
            logger.warning(f"Could not search vector store: {e}. Using base context.")

        user_prompt = KNOWLEDGE_USER_PROMPT.format(
            query=dispatch_query,
            context=context
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
            }
        except Exception as e:
            logger.error(f"Knowledge agent execution failed: {e}")
            return {
                "result": "ज्ञान कोषमा खोज गर्दा प्राविधिक त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
