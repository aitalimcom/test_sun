import logging
import json
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.calendar import CALENDAR_SYSTEM_PROMPT, CALENDAR_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class CalendarAgent(BaseAgent):
    """Manages scheduling of agricultural tasks, calendars, and milestones."""

    name = "calendar"
    description = "कार्यसूची प्रबन्धक - किसानको कामको योजना बनाउने, थप्ने र सम्पादन गर्ने कार्य"
    model_preference = "default"

    @property
    def system_prompt(self) -> str:
        return CALENDAR_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Calendar agent...")
        dispatch_query = state.get("dispatch_query", "")

        tasks_list = "हाल कार्यसूची खाली छ।"

        try:
            from db.tasks import tasks_db
            tasks = tasks_db.list_tasks()
            if tasks:
                tasks_list = json.dumps(tasks, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Could not load calendar database: {e}. Using mock/empty list.")

        user_prompt = CALENDAR_USER_PROMPT.format(
            query=dispatch_query,
            tasks=tasks_list
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
            logger.error(f"Calendar agent execution failed: {e}")
            return {
                "result": "कार्यसूची अद्यावधिक गर्दा प्राविधिक त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
