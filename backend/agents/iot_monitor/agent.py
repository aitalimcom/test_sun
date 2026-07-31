"""Agent 3: Monitor Agent — threshold checks, alert generation, cron-based monitoring."""
import httpx
import json
import logging
from config import settings
from db import iot_db
from data.iot_defaults import DEFAULT_THRESHOLDS

logger = logging.getLogger(__name__)

MONITOR_SYSTEM_PROMPT = """You are a monitoring agent for a farming IoT system called Krishi Sewa.

Your job is to:
1. Check sensor readings against thresholds
2. Generate alerts when readings are out of safe range
3. Create task entries for the farmer
4. Provide monitoring summaries

THRESHOLD RULES:
- temperature: 10°C - 40°C (below = frost risk, above = heat stress)
- humidity: 20% - 90% (below = drought risk, above = fungal risk)
- co2: 0 - 800 ppm (above = poor ventilation)
- moisture: 20% - 80% (below = needs irrigation, above = waterlogged)
- ph: 5.5 - 8.0 (outside = nutrient deficiency risk)

SEVERITY LEVELS:
- info: within normal range but noteworthy
- warning: approaching threshold, monitor closely
- critical: exceeded threshold, immediate action needed

RESPONSE FORMAT — return ONLY a JSON object:
{
  "alerts": [
    {
      "device_id": "xxx",
      "metric": "moisture",
      "value": 18.5,
      "threshold": "< 20%",
      "severity": "critical",
      "message": "Soil moisture critically low at 18.5%. Irrigation recommended."
    }
  ],
  "tasks": [
    {
      "title": "Irrigate field at location X",
      "priority": "high",
      "description": "Moisture level dropped below 20% threshold"
    }
  ],
  "summary": "Monitoring complete: 2 alerts generated, 1 task created.",
  "monitoring_schedule": {
    "recommended": true,
    "frequency": "daily",
    "time": "06:00",
    "description": "Daily morning check recommended for optimal crop health"
  }
}

RULES:
- Check ALL devices, not just one
- Be specific about which device has which issue
- For tasks, include actionable descriptions
- Suggest monitoring schedule based on device types and readings
- If all readings are normal, return empty alerts array with a positive summary"""


async def run_monitor_check() -> dict:
    """Run a monitoring check across all devices. Called by cron."""
    devices = iot_db.list_devices()
    if not devices:
        return {"alerts": [], "tasks": [], "summary": "No devices registered."}

    if not settings.openrouter_api_key:
        # Fallback: rule-based check without LLM
        return await _rule_based_check(devices)

    # Build context with all device data
    context_parts = []
    for d in devices:
        device_id = d["device_id"]
        sensors = json.loads(d.get("sensors_json", "[]"))
        latest = iot_db.get_latest_telemetry(device_id)
        if latest:
            readings = {k: v for k, v in latest.items() if k != "timestamp"}
            context_parts.append(f"Device '{d['name']}' ({device_id}, {d['device_type']}): {json.dumps(readings)}")
        else:
            context_parts.append(f"Device '{d['name']}' ({device_id}): no telemetry data")

    prompt = f"""Analyze the following sensor readings and generate alerts if any thresholds are exceeded.

DEVICE READINGS:
{chr(10).join(context_parts)}

THRESHOLDS:
{json.dumps(DEFAULT_THRESHOLDS, indent=2)}

Respond with a JSON object containing alerts, tasks, summary, and monitoring_schedule."""

    messages = [
        {"role": "system", "content": MONITOR_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    payload = {
        "model": settings.openrouter_model,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2048,
    }

    try:
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

        result = json.loads(content)

        # Store alerts in CSV
        for alert_data in result.get("alerts", []):
            iot_db.create_alert(
                device_id=alert_data["device_id"],
                metric=alert_data["metric"],
                value=alert_data["value"],
                threshold=alert_data["threshold"],
                severity=alert_data["severity"],
                message=alert_data["message"],
            )

        return result

    except Exception as e:
        logger.error(f"Monitor agent error: {e}")
        return await _rule_based_check(devices)


async def _rule_based_check(devices: list[dict]) -> dict:
    """Fallback rule-based monitoring without LLM."""
    alerts = []
    tasks = []

    for d in devices:
        device_id = d["device_id"]
        latest = iot_db.get_latest_telemetry(device_id)
        if not latest:
            continue

        for metric, value_str in latest.items():
            if metric == "timestamp":
                continue
            try:
                value = float(value_str)
            except (ValueError, TypeError):
                continue

            thresholds = DEFAULT_THRESHOLDS.get(metric)
            if not thresholds:
                continue

            if value < thresholds["min"] or value > thresholds["max"]:
                severity = thresholds["severity"]
                direction = "below" if value < thresholds["min"] else "above"
                msg = f"{metric} {direction} threshold: {value} (safe: {thresholds['min']}-{thresholds['max']})"
                alert = iot_db.create_alert(
                    device_id=device_id,
                    metric=metric,
                    value=value,
                    threshold=f"{thresholds['min']}-{thresholds['max']}",
                    severity=severity,
                    message=msg,
                )
                alerts.append(alert)
                tasks.append({
                    "title": f"Address {metric} alert on {d['name']}",
                    "priority": severity,
                    "description": msg,
                })

    battery_alerts = []
    for d in devices:
        battery = int(d.get("battery", 100))
        if battery < 20:
            battery_alerts.append({
                "device_id": d["device_id"],
                "metric": "battery",
                "value": battery,
                "threshold": "< 20%",
                "severity": "warning",
                "message": f"Battery low on {d['name']}: {battery}%",
            })

    return {
        "alerts": alerts + battery_alerts,
        "tasks": tasks,
        "summary": f"Rule-based check: {len(alerts)} sensor alerts, {len(battery_alerts)} battery alerts.",
    }
