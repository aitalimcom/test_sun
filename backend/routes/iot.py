"""IoT REST API — devices, telemetry, config, alerts, sync, mock data."""
import json
import logging
import random
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Any

from db import iot_db
from data.iot_defaults import SENSOR_TYPES, ACTUATOR_TYPES, DEFAULT_THRESHOLDS
from models.iot import (
    DeviceRegisterRequest, DeviceUpdateRequest, TelemetryData,
    IoTActionRequest, AlertCreateRequest, ScheduleCreateRequest,
    CronJobUpdate,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/iot", tags=["IoT"])


# ── Devices ──

@router.get("/devices")
async def list_devices() -> Any:
    devices = iot_db.list_devices()
    # Parse JSON fields for response
    for d in devices:
        d["sensors"] = json.loads(d.get("sensors_json", "[]"))
        d["actuators"] = json.loads(d.get("actuators_json", "[]"))
        d["config"] = json.loads(d.get("config_json", "{}"))
        d.pop("sensors_json", None)
        d.pop("actuators_json", None)
        d.pop("config_json", None)
    return {"devices": devices}


@router.get("/devices/{device_id}")
async def get_device(device_id: str) -> Any:
    device = iot_db.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device["sensors"] = json.loads(device.get("sensors_json", "[]"))
    device["actuators"] = json.loads(device.get("actuators_json", "[]"))
    device["config"] = json.loads(device.get("config_json", "{}"))
    device.pop("sensors_json", None)
    device.pop("actuators_json", None)
    device.pop("config_json", None)
    # Attach latest telemetry
    device["latest"] = iot_db.get_latest_telemetry(device_id)
    return {"device": device}


@router.post("/devices")
async def register_device(req: DeviceRegisterRequest) -> Any:
    # Check if device with same name exists
    existing = iot_db.list_devices()
    for d in existing:
        if d["name"] == req.name:
            raise HTTPException(status_code=400, detail="Device with this name already exists")

    device_id = f"dev-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    device = iot_db.register_device(
        device_id=device_id,
        name=req.name,
        device_type=req.device_type,
        location=req.location,
        sensors=req.sensors,
        actuators=req.actuators,
        config=req.config,
        battery=req.battery,
        lat=req.lat,
        lng=req.lng,
    )
    logger.info(f"Registered device: {device_id} ({req.name})")
    return {"device": device, "message": f"Device '{req.name}' registered successfully"}


@router.put("/devices/{device_id}")
async def update_device(device_id: str, req: DeviceUpdateRequest) -> Any:
    device = iot_db.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    updates = {}
    if req.name is not None:
        updates["name"] = req.name
    if req.location is not None:
        updates["location"] = req.location
    if req.status is not None:
        updates["status"] = req.status
    if req.config is not None:
        updates["config_json"] = json.dumps(req.config)
    updated = iot_db.update_device(device_id, updates)
    return {"device": updated}


@router.delete("/devices/{device_id}")
async def delete_device(device_id: str) -> Any:
    if not iot_db.get_device(device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    iot_db.delete_device(device_id)
    return {"message": f"Device {device_id} deleted"}


# ── Telemetry ──

@router.get("/device/{device_id}/telemetry")
async def get_telemetry(device_id: str, limit: int = 100) -> Any:
    if not iot_db.get_device(device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    rows = iot_db.get_telemetry(device_id, limit=limit)
    # Parse float values
    for row in rows:
        for k, v in row.items():
            if k != "timestamp":
                try:
                    row[k] = float(v)
                except (ValueError, TypeError):
                    pass
    return {"device_id": device_id, "telemetry": rows, "count": len(rows)}


@router.post("/device/{device_id}/telemetry")
async def post_telemetry(device_id: str, req: TelemetryData) -> Any:
    if not iot_db.get_device(device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    iot_db.append_telemetry(device_id, req.data)
    return {"status": "ok"}


@router.post("/device/{device_id}/sync")
async def sync_device(device_id: str) -> Any:
    """Sync device — generates mock telemetry data based on device sensors."""
    device = iot_db.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    sensors = json.loads(device.get("sensors_json", "[]"))
    actuators = json.loads(device.get("actuators_json", "[]"))
    data = _generate_mock_reading(device["device_type"], sensors, actuators)
    iot_db.append_telemetry(device_id, data)
    # Update battery
    battery = int(device.get("battery", 100))
    iot_db.update_device(device_id, {"battery": str(max(0, battery - 1))})
    return {"device_id": device_id, "data": data, "synced_at": datetime.now().isoformat()}


# ── Config ──

@router.get("/device/{device_id}/config")
async def get_device_config(device_id: str) -> Any:
    device = iot_db.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    config = json.loads(device.get("config_json", "{}"))
    return {"device_id": device_id, "config": config}


@router.post("/device/{device_id}/config")
async def update_device_config(device_id: str, config: dict[str, Any]) -> Any:
    device = iot_db.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    existing = json.loads(device.get("config_json", "{}"))
    existing.update(config)
    iot_db.update_device(device_id, {"config_json": json.dumps(existing)})
    return {"device_id": device_id, "config": existing}


# ── Actions ──

@router.post("/device/{device_id}/action")
async def trigger_action(device_id: str, req: IoTActionRequest) -> Any:
    device = iot_db.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    logger.info(f"Action '{req.action}' on device '{device_id}' params={req.params}")
    # Store action in config
    config = json.loads(device.get("config_json", "{}"))
    config[f"last_action_{req.action}"] = datetime.now().isoformat()
    if req.params:
        config[f"action_params_{req.action}"] = req.params
    iot_db.update_device(device_id, {"config_json": json.dumps(config)})
    return {
        "status": "executed",
        "device_id": device_id,
        "action": req.action,
        "params": req.params,
    }


# ── Alerts ──

@router.get("/alerts")
async def list_alerts(status: str | None = None) -> Any:
    alerts = iot_db.list_alerts(status=status)
    return {"alerts": alerts, "count": len(alerts)}


@router.post("/alerts")
async def create_alert(req: AlertCreateRequest) -> Any:
    alert = iot_db.create_alert(
        device_id=req.device_id,
        metric=req.metric,
        value=req.value,
        threshold=req.threshold,
        severity=req.severity,
        message=req.message,
    )
    return {"alert": alert}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str) -> Any:
    if iot_db.resolve_alert(alert_id):
        return {"message": "Alert resolved"}
    raise HTTPException(status_code=404, detail="Alert not found")


# ── Schedules ──

@router.get("/schedules")
async def list_schedules(device_id: str | None = None) -> Any:
    schedules = iot_db.list_schedules(device_id=device_id)
    for s in schedules:
        s["params"] = json.loads(s.pop("params_json", "{}"))
    return {"schedules": schedules}


@router.post("/schedules")
async def create_schedule(req: ScheduleCreateRequest) -> Any:
    schedule = iot_db.create_schedule(
        device_id=req.device_id,
        action=req.action,
        params=req.params,
        cron_expr=req.cron_expr,
    )
    return {"schedule": schedule}


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str) -> Any:
    if iot_db.delete_schedule(schedule_id):
        return {"message": "Schedule deleted"}
    raise HTTPException(status_code=404, detail="Schedule not found")


# ── Sensor/Actuator type info ──

@router.get("/types/sensors")
async def get_sensor_types() -> Any:
    return {"sensors": SENSOR_TYPES}


@router.get("/types/actuators")
async def get_actuator_types() -> Any:
    return {"actuators": ACTUATOR_TYPES}


@router.get("/types/devices")
async def get_device_presets() -> Any:
    from data.iot_defaults import DEVICE_PRESETS
    return {"presets": DEVICE_PRESETS}


# ── Mock data generator ──

def _generate_mock_reading(device_type: str, sensors: list[str], actuators: list[str]) -> dict:
    """Generate realistic mock sensor readings based on device type."""
    data = {}
    now = datetime.now()
    hour = now.hour

    for s in sensors:
        if s == "temperature":
            # Diurnal cycle: cooler at night, warmer during day
            base = 22.0 + 8.0 * max(0, min(1, (hour - 6) / 6)) * (1 - max(0, min(1, (hour - 14) / 8)))
            data["temperature"] = round(base + random.uniform(-2.0, 2.0), 1)
        elif s == "humidity":
            base = 65.0 - 20.0 * max(0, min(1, (hour - 6) / 6)) * (1 - max(0, min(1, (hour - 14) / 8)))
            data["humidity"] = round(max(20.0, min(95.0, base + random.uniform(-5.0, 5.0))), 1)
        elif s == "co2":
            data["co2"] = round(random.uniform(380.0, 480.0), 1)
        elif s == "moisture":
            data["moisture"] = round(random.uniform(25.0, 75.0), 1)
        elif s == "ph":
            data["ph"] = round(random.uniform(5.8, 7.5), 2)
        elif s == "light":
            if 6 <= hour <= 18:
                data["light"] = round(random.uniform(500.0, 80000.0), 0)
            else:
                data["light"] = round(random.uniform(0.0, 50.0), 0)
        elif s == "pressure":
            data["pressure"] = round(random.uniform(1010.0, 1025.0), 1)
        elif s == "rainfall":
            data["rainfall"] = round(random.choice([0.0, 0.0, 0.0, 0.5, 1.2, 3.0]), 1)
        else:
            data[s] = round(random.uniform(0.0, 100.0), 1)

    for a in actuators:
        if a in ("pump", "light", "fan", "valve"):
            data[a] = random.choice(["on", "off"])
        elif a in ("ac", "heater"):
            data[a] = round(random.uniform(20.0, 28.0), 1)
        else:
            data[a] = "off"

    return data
