import logging
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.disease import DISEASE_SYSTEM_PROMPT, DISEASE_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class DiseaseAgent(BaseAgent):
    """Diagnoses crop diseases from symptoms and image analyses."""

    name = "disease"
    description = "बाली रोग विशेषज्ञ - बालीमा लाग्ने रोग तथा कीराहरूको पहिचान र रासायनिक तथा जैविक उपचार"
    model_preference = "vision"  # Prefer vision model

    @property
    def system_prompt(self) -> str:
        return DISEASE_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Disease agent...")
        dispatch_query = state.get("dispatch_query", "")
        
        # Get crop type if available from query or state
        crop = state.get("processed_input", {}).get("detected_entities", ["सामान्य बाली"])
        if isinstance(crop, list) and crop:
            crop_str = crop[0]
        else:
            crop_str = "बाली"
            
        analyses = state.get("image_analyses", [])
        
        user_prompt = DISEASE_USER_PROMPT.format(
            crop=crop_str,
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
            logger.error(f"Disease agent execution failed: {e}")
            return {
                "result": "रोग निदान प्रक्रियामा प्राविधिक त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
