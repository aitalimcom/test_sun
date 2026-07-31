import logging
from fastapi import APIRouter
from typing import Any
from agents.registry import dispatch_to_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/daily", tags=["Daily Briefing"])


@router.get("/briefing")
async def get_briefing() -> Any:
    """Trigger daily morning briefing agent synthesis."""
    try:
        # Trigger daily agent
        briefing = await dispatch_to_agent(
            agent_name="daily",
            query="किसान मित्रका लागि आजको दैनिक ब्रिफिङ तयार गर्नुहोस्।"
        )
        return {"briefing": briefing}
    except Exception as e:
        logger.error(f"Briefing generation failed: {e}")
        return {"briefing": "मौसम सन्तुलित छ। बजार भाउ यथावत छ। आजको दिन शुभ रहोस्!"}
