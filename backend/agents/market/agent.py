import logging
from typing import Any
from core.agent import BaseAgent
from core.state import AgentState
from prompts.templates.market import MARKET_SYSTEM_PROMPT, MARKET_USER_PROMPT
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


class MarketAgent(BaseAgent):
    """Provides crop market prices and mandi advisory."""

    name = "market"
    description = "बजार भाउ विशेषज्ञ - कालीमाटी लगायतका बजारको तरकारी तथा फलफूलको मूल्य विश्लेषण"
    model_preference = "default"

    @property
    def system_prompt(self) -> str:
        return MARKET_SYSTEM_PROMPT

    async def execute(self, state: AgentState) -> dict[str, Any]:
        logger.info("Executing Market agent...")
        dispatch_query = state.get("dispatch_query", "")

        # Default mock price data
        market_data = (
            "कालीमाटी फलफूल तथा तरकारी बजार दर:\n"
            "- आलु (रातो): रु ६० - ७० प्रति केजी\n"
            "- गोलभेडा (ठूलो): रु ८० - ९० प्रति केजी\n"
            "- बन्दा: रु ३० - ३५ प्रति केजी\n"
            "- काउली (स्थानीय): रु ७० - ८० प्रति केजी\n"
            "- प्याज (सुकेको): रु १२० - १३० प्रति केजी"
        )

        try:
            from db.market import market_db
            prices = market_db.get_latest_prices()
            if prices:
                market_data = "\n".join([f"- {p['crop']}: रु {p['min_price']} - {p['max_price']} प्रति {p['unit']}" for p in prices])
        except Exception as e:
            logger.warning(f"Could not load market database: {e}. Using mock market rates.")

        user_prompt = MARKET_USER_PROMPT.format(
            query=dispatch_query,
            market_data=market_data
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
            logger.error(f"Market agent execution failed: {e}")
            return {
                "result": "बजार मूल्य विवरण तयार गर्दा त्रुटि भयो।",
                "success": False,
                "error": str(e),
            }
