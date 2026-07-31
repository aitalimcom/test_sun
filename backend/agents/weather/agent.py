import logging
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.weather import WEATHER_SYSTEM_PROMPT, WEATHER_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class WeatherAgent(BaseAgent):
    """Provides weather advisories and spray indices based on forecast data."""

    name = "weather"
    description = "मौसम सल्लाहकार - मौसम पूर्वानुमान विश्लेषण र बालीमा औषधी छर्कने उपयुक्त समयको सल्लाह"
    model_preference = "default"

    @property
    def system_prompt(self) -> str:
        return WEATHER_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Weather agent...")
        dispatch_query = state.get("dispatch_query", "")
        
        # Get coordinates or use defaults (Kathmandu)
        lat = 27.7172
        lng = 85.3240
        
        # Call the weather service
        current_weather = "तापक्रम: २६°C, अवस्था: आंशिक बदली, सापेक्षित आद्रता: ७५%, हावाको गति: ८ कि.मी./घण्टा"
        forecast = (
            "आज: हल्का वर्षाको सम्भावना।\n"
            "भोलि: मौसम सफा रहने।\n"
            "पर्सि: आंशिक बदली।"
        )
        
        try:
            from services.weather.openweather import weather_service
            data = await weather_service.get_weather_and_forecast(lat, lng)
            if data:
                current_weather = data.get("current_str", current_weather)
                forecast = data.get("forecast_str", forecast)
        except Exception as e:
            logger.warning(f"Could not load real weather service: {e}. Using mock weather.")

        user_prompt = WEATHER_USER_PROMPT.format(
            location=f"Latitude: {lat}, Longitude: {lng}",
            current_weather=current_weather,
            forecast=forecast,
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
            logger.error(f"Weather agent execution failed: {e}")
            return {
                "result": "मौसम विश्लेषण सल्लाह तयार गर्दा त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
        
        return {"result": "Weather information", "success": True}
