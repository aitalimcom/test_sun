"""Agent 1: Add-Device Chat — user describes what they have, Gemma generates device config + ESP32 code."""
import httpx
import json
import logging
from config import settings
from data.iot_defaults import SENSOR_TYPES, ACTUATOR_TYPES, DEVICE_PRESETS

logger = logging.getLogger(__name__)

ADD_DEVICE_SYSTEM_PROMPT = """You are an IoT device configuration assistant for a farming system called Krishi Sewa.

The farmer will describe what sensors and actuators they have. You help them:
1. Identify the correct sensor/actuator types from our catalog
2. Generate a device configuration (name, type, sensors, actuators, pin assignments)
3. Generate complete ESP32 Arduino code for their device

AVAILABLE SENSORS (inputs — float values prioritized):
- temperature: DHT22/DS18B20, pin A0, unit °C
- humidity: DHT22, pin A1, unit %
- co2: MQ-135/MH-Z19, pin A2, unit ppm
- moisture: Capacitive soil sensor, pin A3, unit %
- ph: Analog pH probe, pin A4, unit pH
- light: BH1750, pin A5, unit lux
- pressure: BMP280 (I2C), unit hPa
- rainfall: Tipping bucket, pin D8, unit mm

AVAILABLE ACTUATORS (outputs):
- pump: Relay, pin D2, on/off toggle
- ac: AC/Cooler, pin D3, range 15-40°C (desired temp)
- light: Grow light relay, pin D4, on/off toggle
- fan: Ventilation relay, pin D5, on/off toggle
- valve: Irrigation solenoid, pin D6, open/close
- heater: Heating element, pin D7, range 15-45°C

DEVICE PRESETS:
- weather: Weather Station — temp, humidity, co2 sensors
- soil: Soil Monitor — moisture, temp, ph + pump, valve
- greenhouse: Greenhouse Controller — temp, humidity, co2, light + fan, ac, light, heater
- irrigation: Smart Irrigation — moisture, temp, rainfall + pump, valve

PIN RULES:
- Sensors use analog pins A0-A5 (or I2C for digital sensors)
- Actuators use digital pins D2-D7
- DHT22 shares one pin for temp+humidity
- Never assign same pin to two different sensors

RESPONSE FORMAT — return ONLY a JSON object:
{
  "device_name": "name the device",
  "device_type": "weather|soil|greenhouse|irrigation|custom",
  "description": "brief description of what this device does",
  "sensors": ["temperature", "humidity", ...],
  "actuators": ["pump", "valve", ...],
  "pin_assignments": {"sensor_name": "pin", "actuator_name": "pin"},
  "esp32_code": "complete Arduino .ino code as a string",
  "connection_notes": "simple wiring instructions",
  "follow_up": "suggested next question for the farmer"
}

ESP32 CODE REQUIREMENTS:
- Use #define for DEVICE_ID (placeholder "DEVICE_ID_HERE") and SERVER_URL (placeholder "http://YOUR_SERVER:8000")
- Include WiFi.h and HTTPClient.h
- POST sensor data as JSON to SERVER_URL/api/iot/device/DEVICE_ID/telemetry
- Poll SERVER_URL/api/iot/device/DEVICE_ID/config every 5 seconds for actuator commands
- Use proper Arduino library includes (DHT.h, Wire.h, etc.)
- Include setup() with WiFi connect and sensor init
- Include loop() with postSensorData() and pollCommands()
- Add 10-second SYNC_INTERVAL between readings
- Code should be complete, compilable, and well-structured
- Add comments explaining wiring for each sensor/actuator

FOLLOW-UP QUESTIONS:
After generating the config, suggest a relevant follow-up like:
- "Would you like me to adjust the sensor thresholds?"
- "Should I set up automatic monitoring alerts?"
- "Do you want to schedule this device to sync at specific intervals?"
"""


async def chat_add_device(message: str, history: list[dict] | None = None) -> dict:
    """Chat with Gemma to configure a new IoT device."""
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY not configured")

    messages = [{"role": "system", "content": ADD_DEVICE_SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})

    payload = {
        "model": settings.openrouter_model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4096,
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
            "device_name": "Custom Device",
            "device_type": "custom",
            "description": content[:200],
            "sensors": [],
            "actuators": [],
            "esp32_code": None,
            "follow_up": content,
        }

    return result
