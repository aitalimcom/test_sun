import logging
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.bajar import BAJAR_SYSTEM_PROMPT, BAJAR_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class BajarAgent(BaseAgent):
    """Deep reasoning model that analyzes seasonal crop price fluctuations and forecasts demand."""

    name = "bajar"
    description = "बजार अन्तर्दृष्टि - बालीको मूल्य विश्लेषण, आगामी महिनाको बजार भाउ पूर्वानुमान"
    model_preference = "reasoning"  # Prefer heavier reasoning model (e.g. thinking mode)

    @property
    def system_prompt(self) -> str:
        return BAJAR_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Bajar deep reasoning agent...")
        dispatch_query = state.get("dispatch_query", "")

        historical_prices = (
            "विगतका महिनाहरूको भाउ:\n"
            "- गोलभेडा: जेठ (रु ४०), असार (रु ५५), साउन (रु ८०)\n"
            "- आलु: जेठ (रु ४५), असार (रु ५०), साउन (रु ६५)"
        )

        user_prompt = BAJAR_USER_PROMPT.format(
            query=dispatch_query,
            historical_prices=historical_prices
        )

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_prompt)
        ]

        try:
            # Trigger thinking mode if supported (passed as a system capability or option by LLM class)
            response = await self.llm.ainvoke(messages)
            content = response.content.strip()
            return {
                "result": content,
                "success": True,
                "new_messages": [{"role": "assistant", "content": content}],
            }
        except Exception as e:
            logger.error(f"Bajar agent execution failed: {e}")
            return {
                "result": "बजार भाउ पूर्वानुमान विश्लेषण गर्दा प्राविधिक त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
