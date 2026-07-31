import logging
from fastapi import APIRouter, HTTPException
from typing import Any

from db.iot_devices import iot_devices_db
from models.iot import IoTActionRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/iot", tags=["IoT"])


@router.get("/devices")
async def list_devices() -> Any:
    """List registered IoT telemetry devices."""
    devices = iot_devices_db.list_devices()
    # Seed mock if empty
    if not devices:
        from data.iot_mock import IOT_DEVICES
        for d in IOT_DEVICES:
            iot_devices_db.register_device(
                device_id=d["id"],
                name=d["name"],
                device_type=d["deviceType"],
                land_id=d.get("landId", "land-1"),
                metrics=d.get("metrics", [])
            )
        devices = iot_devices_db.list_devices()
    return {"devices": devices}


@router.post("/action")
async def trigger_action(request: IoTActionRequest) -> Any:
    """Execute valve controller or telemetry actions."""
    device = iot_devices_db.get(request.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
        
    logger.info(f"Triggering action '{request.action}' on device '{request.device_id}'")
    
    # Simulate valve toggle
    if request.action == "toggle_valve":
        metrics = device.get("metrics", [])
        for m in metrics:
            if m.get("label") == "Valve State":
                current = m.get("value")
                m["value"] = "Open" if current == "Closed" else "Closed"
        iot_devices_db.update_metrics(request.device_id, metrics)
        
    return {
        "status": "success",
        "device_id": request.device_id,
        "action": request.action,
        "current_state": iot_devices_db.get(request.device_id)
    }
