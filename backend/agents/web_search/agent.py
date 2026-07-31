import logging
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.web_search import WEB_SEARCH_SYSTEM_PROMPT, WEB_SEARCH_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class WebSearchAgent(BaseAgent):
    """Searches the internet for real-time news and Summarizes it in Nepali."""

    name = "web_search"
    description = "वेब खोजकर्ता - ताजा कृषि समाचार, नवीनतम कृषि प्रविधि वा अनलाइन बजारको खोज"
    model_preference = "default"

    @property
    def system_prompt(self) -> str:
        return WEB_SEARCH_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Web Search agent...")
        dispatch_query = state.get("dispatch_query", "")

        search_results = "वेब खोजबाट कुनै नतिजा फेला परेन।"

        # Perform DuckDuckGo search
        try:
            from services.search.web_search import web_search_service
            results = await web_search_service.search(dispatch_query, max_results=3)
            if results:
                search_results = "\n\n".join([f"शीर्षक: {r.get('title')}\nलिङ्क: {r.get('link')}\nविवरण: {r.get('snippet')}" for r in results])
        except Exception as e:
            logger.warning(f"Could not perform web search: {e}. Using mock message.")

        user_prompt = WEB_SEARCH_USER_PROMPT.format(
            query=dispatch_query,
            search_results=search_results
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
            logger.error(f"Web search agent execution failed: {e}")
            return {
                "result": "वेब खोज जानकारी संकलन गर्दा प्राविधिक त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
