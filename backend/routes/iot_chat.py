"""
IoT Chat API — two specialized AI agents for device configuration and device control.
Executes actuator state updates, threshold alerts creation, and cron task scheduling.
"""
import json
import logging
from typing import Any
from fastapi import APIRouter, HTTPException

from models.iot import ChatMessage
from db import iot_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/iot/chat", tags=["IoT Chat"])


@router.post("/add-device")
async def chat_add_device(req: ChatMessage) -> Any:
    """Chat with Agent 1: Add-device configuration assistant."""
    try:
        from agents.iot_device.agent import chat_add_device as _chat
        result = await _chat(req.message, history=req.history or None)
        return result
    except Exception as e:
        logger.error(f"Add-device chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/control/{device_id}")
async def chat_control(device_id: str, req: ChatMessage) -> Any:
    """Chat with Agent 2: Device control & actuator management."""
    try:
        from agents.iot_control.agent import chat_control as _chat
        result = await _chat(req.message, device_id=device_id, history=req.history or None)

        target_device = iot_db.get_device(device_id)
        if target_device:
            config = json.loads(target_device.get("config_json") or "{}")
            actuators_state = config.get("actuators_state", {})

            # 1. Execute Actuator Actions
            actions = result.get("actions", [])
            for action in actions:
                act = action.get("action", "")
                params = action.get("params", {})
                
                # Parse common actions like start_pump, valve_open, fan_on, set_ac_temp
                if "pump" in act:
                    actuators_state["pump"] = "on" if "start" in act or "on" in act else "off"
                elif "valve" in act:
                    actuators_state["valve"] = "open" if "open" in act or "on" in act else "closed"
                elif "fan" in act:
                    actuators_state["fan"] = "on" if "on" in act else "off"
                elif "light" in act:
                    actuators_state["light"] = "on" if "on" in act else "off"
                elif "heater" in act:
                    actuators_state["heater"] = params.get("temperature", 25)
                elif "ac" in act:
                    actuators_state["ac"] = params.get("temperature", 22)

                # Log execution into CSV telemetry
                iot_db.append_telemetry(device_id, {act: "executed", **params})

            # Update persisted device config
            config["actuators_state"] = actuators_state
            iot_db.update_device(device_id, {"config_json": json.dumps(config)})

        # 2. Create Alerts if threshold warning generated
        for alert_item in result.get("alerts", []):
            iot_db.create_alert(
                device_id=device_id,
                metric=alert_item.get("metric", "system"),
                value=alert_item.get("value", 0.0),
                threshold=str(alert_item.get("threshold", "limit_exceeded")),
                severity=alert_item.get("severity", "warning"),
                message=alert_item.get("message", "Threshold alert triggered via control chat."),
            )

        # 3. Create Schedule if returned
        schedule = result.get("schedule")
        if schedule:
            iot_db.create_schedule(
                device_id=schedule.get("device_id", device_id),
                action=schedule.get("action", "start_pump"),
                params=schedule.get("params", {}),
                cron_expr=schedule.get("cron_expr", "0 6 * * *"),
            )

        return result
    except Exception as e:
        logger.error(f"Control chat error for {device_id}: {e}")
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
