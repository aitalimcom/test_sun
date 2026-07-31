import logging
import json
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.iot import IOT_SYSTEM_PROMPT, IOT_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class IoTAgent(BaseAgent):
    """Manages IoT telemetry, valve actuator commands, and battery levels."""

    name = "iot"
    description = "आईओटी उपकरण प्रबन्धक - माटोको चिस्यान, तापक्रम र सिँचाइ भल्भ नियन्त्रण प्रणाली"
    model_preference = "default"

    @property
    def system_prompt(self) -> str:
        return IOT_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing IoT agent...")
        dispatch_query = state.get("dispatch_query", "")

        # Default telemetry mock
        device_data = (
            "उपकरण १: गुण्डु NPK प्रोब (NPK Probe) - सुचारु (active), ब्याट्री ८८%\n"
            "- नाइट्रोजन: 45 mg/kg, फस्फोरस: 32 mg/kg, पोटासियम: 60 mg/kg\n"
            "उपकरण २: लुभु माटो प्रोब (Soil Moisture Probe) - चेतावनी (warning), ब्याट्री ४२%\n"
            "- माटोको चिस्यान: २४%, माटोको तापक्रम: २६.८°C\n"
            "उपकरण ३: चोभर भल्भ कन्ट्रोलर (Irrigation Valve) - बन्द (offline), ब्याट्री ०%"
        )

        try:
            from data.iot_mock import IOT_DEVICES
            device_data = json.dumps(IOT_DEVICES, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Could not load IoT mock data module: {e}. Using mock string.")

        user_prompt = IOT_USER_PROMPT.format(
            query=dispatch_query,
            device_data=device_data
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
            logger.error(f"IoT agent execution failed: {e}")
            return {
                "result": "आईओटी उपकरण जाँच गर्दा प्राविधिक त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
