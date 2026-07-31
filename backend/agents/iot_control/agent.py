"""Agent 2: Control Chat — actuator commands, scheduling, device summaries."""
import httpx
import json
import logging
from config import settings
from db import iot_db

logger = logging.getLogger(__name__)

CONTROL_SYSTEM_PROMPT = """You are a device control assistant for a farming IoT system called Krishi Sewa.

You help the farmer:
1. Check current sensor readings from their devices
2. Control actuators (turn pump on/off, set AC temperature, etc.)
3. Schedule device actions (e.g., "run pump for 50 minutes")
4. Get summaries of device status

AVAILABLE ACTUATOR COMMANDS:
- pump: {"action": "start_pump", "duration_min": N} or {"action": "stop_pump"}
- ac: {"action": "set_ac_temp", "temperature": N} (N = 15-40°C)
- light: {"action": "light_on"} or {"action": "light_off"}
- fan: {"action": "fan_on"} or {"action": "fan_off"}
- valve: {"action": "valve_open"} or {"action": "valve_close"}
- heater: {"action": "set_heater_temp", "temperature": N} (N = 15-45°C)

SCHEDULING:
- Daily: {"schedule": true, "cron": "0 6 * * *", "action": "start_pump", "duration_min": 30}
- Every N minutes: {"schedule": true, "interval_min": N, "action": "start_pump", "duration_min": N}
- One-time: {"schedule": true, "time": "HH:MM", "action": "start_pump", "duration_min": N}

RESPONSE FORMAT — return ONLY a JSON object:
{
  "reply": "human-readable response to the farmer",
  "actions": [
    {"device_id": "xxx", "action": "start_pump", "params": {"duration_min": 30}},
    ...
  ],
  "schedule": {
    "device_id": "xxx",
    "action": "start_pump",
    "params": {"duration_min": 30},
    "cron_expr": "*/30 * * * *"
  } | null,
  "summary": {
    "device_id": "xxx",
    "status": "active",
    "battery": 85,
    "latest_readings": {"temperature": 25.3, "humidity": 62.1},
    "actuator_states": {"pump": "off"}
  } | null
}

RULES:
- Always respond in the same language as the farmer (Nepali or English)
- Be concise and practical
- If the farmer asks about readings, provide the summary
- If they want to control something, include the action
- If they want scheduling, include the schedule object
- For irrigation pump: suggest duration based on crop type if known
- Warn if battery is low (<20%)
- If device not found, suggest they check the device list"""


async def chat_control(
    message: str,
    device_id: str | None = None,
    history: list[dict] | None = None,
) -> dict:
    """Chat with Gemma to control IoT devices."""
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY not configured")

    # Build context with device data
    context_parts = []
    if device_id:
        device = iot_db.get_device(device_id)
        if device:
            import json as _json
            sensors = _json.loads(device.get("sensors_json", "[]"))
            actuators = _json.loads(device.get("actuators_json", "[]"))
            latest = iot_db.get_latest_telemetry(device_id)
            context_parts.append(f"Current device: {device['name']} ({device['device_type']})")
            context_parts.append(f"Sensors: {', '.join(sensors)}")
            context_parts.append(f"Actuators: {', '.join(actuators)}")
            if latest:
                context_parts.append(f"Latest readings: {_json.dumps({k:v for k,v in latest.items() if k != 'timestamp'})}")
            context_parts.append(f"Battery: {device.get('battery', 'unknown')}%")
            context_parts.append(f"Status: {device.get('status', 'unknown')}")

    # List all devices for context
    all_devices = iot_db.list_devices()
    if all_devices:
        device_list = ", ".join([f"{d['name']}({d['device_id']})" for d in all_devices])
        context_parts.append(f"All devices: {device_list}")

    system_prompt = CONTROL_SYSTEM_PROMPT
    if context_parts:
        system_prompt += "\n\nCURRENT SYSTEM STATE:\n" + "\n".join(context_parts)

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})

    payload = {
        "model": settings.openrouter_model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 2048,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {
            "reply": content,
            "actions": [],
            "schedule": None,
            "summary": None,
        }

    return result
