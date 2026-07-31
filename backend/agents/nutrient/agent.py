import logging
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.nutrient import NUTRIENT_SYSTEM_PROMPT, NUTRIENT_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class NutrientAgent(BaseAgent):
    """Advises on soil pH, nutrient deficiencies, and organic/chemical fertilizer applications."""

    name = "nutrient"
    description = "माटो तथा मल प्रबन्धक - माटोको गुणस्तर जाँच, NPK स्तर र मल प्रयोग सम्बन्धी सल्लाह"
    model_preference = "default"

    @property
    def system_prompt(self) -> str:
        return NUTRIENT_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Nutrient agent...")
        dispatch_query = state.get("dispatch_query", "")

        # Mock NPK data or look in state if available
        npk_data = "Nitrogen: 45 mg/kg, Phosphorus: 32 mg/kg, Potassium: 60 mg/kg (pH: 6.5)"
        crop_requirements = "Nitrogen: High, Phosphorus: Medium, Potassium: High"

        user_prompt = NUTRIENT_USER_PROMPT.format(
            npk_data=npk_data,
            crop_requirements=crop_requirements,
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
            logger.error(f"Nutrient agent execution failed: {e}")
            return {
                "result": "माटो तथा पोषक तत्व सल्लाह तयार गर्दा त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
