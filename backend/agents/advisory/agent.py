import logging
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.advisory import ADVISORY_SYSTEM_PROMPT, ADVISORY_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class AdvisoryAgent(BaseAgent):
    """Provides deep reasoning agricultural advisories, crop calendars, and irrigation schemes."""

    name = "advisory"
    description = "कृषि सल्लाहकार - माटो अनुकूलता, रोप्ने तालिका र बाली उत्पादन बढाउने सल्लाह"
    model_preference = "reasoning"  # Prefer heavy reasoning/thinking model

    @property
    def system_prompt(self) -> str:
        return ADVISORY_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Farm Advisory expert agent...")
        dispatch_query = state.get("dispatch_query", "")
        processed = state.get("processed_input", {})
        context = processed.get("enriched_context", dispatch_query)

        user_prompt = ADVISORY_USER_PROMPT.format(
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
            logger.error(f"Advisory agent execution failed: {e}")
            return {
                "result": "कृषि सल्लाह विश्लेषण प्रक्रियामा प्राविधिक त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
