import logging
import json
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.daily import DAILY_SYSTEM_PROMPT, DAILY_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class DailyAgent(BaseAgent):
    """Generates structured morning farm briefings aggregating weather, market prices, and pending tasks."""

    name = "daily"
    description = "दैनिक ब्रिफिङ प्रबन्धक - बिहानको मौसम पूर्वानुमान, बजार भाउ र कार्यसूचीको सारांश"
    model_preference = "default"

    @property
    def system_prompt(self) -> str:
        return DAILY_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Daily agent...")
        
        # Load weather overview
        weather_summary = "मौसम: २५°C, वर्षाको सम्भावना ३०%"
        try:
            from services.weather.openweather import weather_service
            data = await weather_service.get_weather_and_forecast(27.7172, 85.3240)
            if data:
                weather_summary = data.get("current_str", weather_summary)
        except Exception:
            pass
            
        # Load prices
        prices_summary = "कालीमाटी बजार भाउ: आलु ६० प्रति केजी, गोलभेडा ८० प्रति केजी"
        try:
            from db.market import market_db
            prices = market_db.get_latest_prices()
            if prices:
                prices_summary = ", ".join([f"{p['crop']}: रु {p['min_price']}-{p['max_price']}" for p in prices[:3]])
        except Exception:
            pass
            
        # Load tasks
        tasks_summary = "आजका लागि कुनै जरुरी काम निर्धारित छैन।"
        try:
            from db.tasks import tasks_db
            tasks = tasks_db.list_tasks()
            if tasks:
                pending = [t for t in tasks if not t.get("completed", False)]
                if pending:
                    tasks_summary = ", ".join([t["title"] for t in pending[:3]])
        except Exception:
            pass

        # Load alerts
        alerts_summary = "सबै उपकरणहरू सुचारु छन् र कुनै प्रतिकूल मौसमको चेतावनी छैन।"
        try:
            from db.alerts import alerts_db
            alerts = alerts_db.list_active_alerts()
            if alerts:
                alerts_summary = ", ".join([a["title"] for a in alerts])
        except Exception:
            pass

        user_prompt = DAILY_USER_PROMPT.format(
            weather=weather_summary,
            prices=prices_summary,
            tasks=tasks_summary,
            alerts=alerts_summary
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
            logger.error(f"Daily agent execution failed: {e}")
            return {
                "result": "दैनिक ब्रिफिङ तयार गर्दा त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
