import logging
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.species import SPECIES_SYSTEM_PROMPT, SPECIES_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class SpeciesAgent(BaseAgent):
    """Identifies crop species, weeds, beneficial insects, or pests."""

    name = "species"
    description = "बाली तथा जीव प्रजाति पहिचान विशेषज्ञ - बालीका जातहरू, झारपात र उपयोगी/हानिकारक कीराहरूको पहिचान"
    model_preference = "vision"

    @property
    def system_prompt(self) -> str:
        return SPECIES_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Species agent...")
        dispatch_query = state.get("dispatch_query", "")
        analyses = state.get("image_analyses", [])
        
        user_prompt = SPECIES_USER_PROMPT.format(
            description=dispatch_query,
            image_analyses=str(analyses)
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
            logger.error(f"Species agent execution failed: {e}")
            return {
                "result": "प्रजाति पहिचान प्रक्रियामा त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
