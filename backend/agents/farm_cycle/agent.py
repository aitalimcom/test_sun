import logging
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.farm_cycle import FARM_CYCLE_SYSTEM_PROMPT, FARM_CYCLE_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class FarmCycleAgent(BaseAgent):
    """Provides planting calendars, crop rotation, and seasonal scheduling guidance."""

    name = "farm_cycle"
    description = "बाली चक्र तथा योजनाविद् - बाली रोप्ने समय, गोडमेल र बाली उठाउने तालिका (बाली पात्रो)"
    model_preference = "default"

    @property
    def system_prompt(self) -> str:
        return FARM_CYCLE_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Farm Cycle agent...")
        dispatch_query = state.get("dispatch_query", "")

        # Guess crop/stage from entities if any
        entities = state.get("processed_input", {}).get("detected_entities", [])
        crop = entities[0] if entities else "बाली"
        stage = "तयारी / रोपाइँ"

        user_prompt = FARM_CYCLE_USER_PROMPT.format(
            crop=crop,
            stage=stage,
            query=dispatch_query
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
            logger.error(f"Farm cycle agent execution failed: {e}")
            return {
                "result": "बाली चक्र योजना विश्लेषण गर्दा त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
