"""IoT Chat API — two separate agents for add-device and control."""
import logging
from fastapi import APIRouter, HTTPException
from typing import Any

from models.iot import ChatMessage
from db import iot_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/iot/chat", tags=["IoT Chat"])


@router.post("/add-device")
async def chat_add_device(req: ChatMessage) -> Any:
    """Chat with Agent 1: Add-device configuration."""
    try:
        from agents.iot_device.agent import chat_add_device as _chat
        result = await _chat(req.message, history=req.history or None)
        return result
    except Exception as e:
        logger.error(f"Add-device chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/control/{device_id}")
async def chat_control(device_id: str, req: ChatMessage) -> Any:
    """Chat with Agent 2: Device control."""
    try:
        from agents.iot_control.agent import chat_control as _chat
        result = await _chat(req.message, device_id=device_id, history=req.history or None)

        # Execute any actions returned
        for action in result.get("actions", []):
            target_id = action.get("device_id", device_id)
            iot_db.append_telemetry(target_id, {action["action"]: "executed"})

        # Create schedule if returned
        schedule = result.get("schedule")
        if schedule:
            iot_db.create_schedule(
                device_id=schedule.get("device_id", device_id),
                action=schedule["action"],
                params=schedule.get("params", {}),
                cron_expr=schedule.get("cron_expr", "0 * * * *"),
            )

        return result
    except Exception as e:
        logger.error(f"Control chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/control")
async def chat_control_general(req: ChatMessage) -> Any:
    """Chat with Agent 2: General control (no specific device)."""
    try:
        from agents.iot_control.agent import chat_control as _chat
        result = await _chat(req.message, history=req.history or None)
        return result
    except Exception as e:
        logger.error(f"Control chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
