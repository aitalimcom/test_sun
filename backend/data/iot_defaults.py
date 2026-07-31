"""IoT sensor and actuator type definitions."""
from typing import Any

# ── Sensor Types (inputs — float values prioritized) ──
SENSOR_TYPES = {
    "temperature": {
        "label": "Temperature",
        "unit": "°C",
        "type": "float",
        "min": -10.0,
        "max": 60.0,
        "pin": "A0",
        "description": "DHT22 or DS18B20 temperature sensor",
    },
    "humidity": {
        "label": "Humidity",
        "unit": "%",
        "type": "float",
        "min": 0.0,
        "max": 100.0,
        "pin": "A1",
        "description": "DHT22 humidity sensor",
    },
    "co2": {
        "label": "CO2",
        "unit": "ppm",
        "type": "float",
        "min": 0.0,
        "max": 2000.0,
        "pin": "A2",
        "description": "MQ-135 or MH-Z19 CO2 sensor",
    },
    "moisture": {
        "label": "Soil Moisture",
        "unit": "%",
        "type": "float",
        "min": 0.0,
        "max": 100.0,
        "pin": "A3",
        "description": "Capacitive soil moisture sensor",
    },
    "ph": {
        "label": "Soil pH",
        "unit": "pH",
        "type": "float",
        "min": 0.0,
        "max": 14.0,
        "pin": "A4",
        "description": "Analog pH sensor probe",
    },
    "light": {
        "label": "Light Intensity",
        "unit": "lux",
        "type": "float",
        "min": 0.0,
        "max": 100000.0,
        "pin": "A5",
        "description": "BH1750 light sensor",
    },
    "pressure": {
        "label": "Atmospheric Pressure",
        "unit": "hPa",
        "type": "float",
        "min": 300.0,
        "max": 1100.0,
        "pin": "I2C",
        "description": "BMP280 pressure sensor",
    },
    "rainfall": {
        "label": "Rainfall",
        "unit": "mm",
        "type": "float",
        "min": 0.0,
        "max": 500.0,
        "pin": "D8",
        "description": "Tipping bucket rain gauge",
    },
}

# ── Actuator Types (outputs) ──
ACTUATOR_TYPES = {
    "pump": {
        "label": "Water Pump",
        "type": "toggle",
        "pin": "D2",
        "description": "Relay-controlled water pump (on/off)",
        "states": ["on", "off"],
    },
    "ac": {
        "label": "AC / Cooler",
        "type": "range",
        "pin": "D3",
        "description": "Air conditioning or evaporative cooler with desired temperature",
        "min": 15,
        "max": 40,
        "unit": "°C",
    },
    "light": {
        "label": "Grow Light",
        "type": "toggle",
        "pin": "D4",
        "description": "Relay-controlled grow light (on/off)",
        "states": ["on", "off"],
    },
    "fan": {
        "label": "Ventilation Fan",
        "type": "toggle",
        "pin": "D5",
        "description": "Relay-controlled exhaust fan (on/off)",
        "states": ["on", "off"],
    },
    "valve": {
        "label": "Irrigation Valve",
        "type": "toggle",
        "pin": "D6",
        "description": "Solenoid valve for irrigation (open/close)",
        "states": ["open", "closed"],
    },
    "heater": {
        "label": "Heater",
        "type": "range",
        "pin": "D7",
        "description": "Heating element with desired temperature",
        "min": 15,
        "max": 45,
        "unit": "°C",
    },
}

# ── Default Thresholds for Alerts ──
DEFAULT_THRESHOLDS = {
    "temperature": {"min": 10.0, "max": 40.0, "severity": "warning"},
    "humidity": {"min": 20.0, "max": 90.0, "severity": "warning"},
    "co2": {"min": 0.0, "max": 800.0, "severity": "warning"},
    "moisture": {"min": 20.0, "max": 80.0, "severity": "critical"},
    "ph": {"min": 5.5, "max": 8.0, "severity": "warning"},
}

# ── Device Type Presets ──
DEVICE_PRESETS = {
    "weather": {
        "name": "Weather Station",
        "sensors": ["temperature", "humidity", "co2"],
        "actuators": [],
        "description": "Basic weather monitoring with temperature, humidity, and CO2",
    },
    "soil": {
        "name": "Soil Monitor",
        "sensors": ["moisture", "temperature", "ph"],
        "actuators": ["pump", "valve"],
        "description": "Soil condition monitoring with irrigation control",
    },
    "greenhouse": {
        "name": "Greenhouse Controller",
        "sensors": ["temperature", "humidity", "co2", "light"],
        "actuators": ["fan", "ac", "light", "heater"],
        "description": "Full greenhouse environment control",
    },
    "irrigation": {
        "name": "Smart Irrigation",
        "sensors": ["moisture", "temperature", "rainfall"],
        "actuators": ["pump", "valve"],
        "description": "Automated irrigation with rain detection",
    },
}
