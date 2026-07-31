"""IoT devices registry database."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from db.base import FileDB
from config import settings


class IoTDevicesDB(FileDB):
    """Manages registered farm IoT devices."""

    def __init__(self) -> None:
        super().__init__(Path(settings.database_root) / "iot", collection_name="iot_devices")

    def register_device(
        self,
        device_id: str,
        name: str,
        device_type: str,  # "NPK" | "Moisture" | "Irrigation" | "Weather"
        land_id: str = "land-1",
        metrics: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Register a new IoT device."""
        record = {
            "id": device_id,
            "name": name,
            "name_np": name,
            "deviceType": device_type,
            "status": "active",
            "battery": 100,
            "metrics": metrics or [],
            "landId": land_id,
            "lastSync": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save(device_id, record)
        return record

    def list_devices(self) -> list[dict[str, Any]]:
        """List registered devices."""
        return self.list_all()

    def update_metrics(self, device_id: str, metrics: list[dict[str, Any]], battery: int | None = None) -> dict[str, Any] | None:
        """Update metrics of a device."""
        device = self.get(device_id)
        if not device:
            return None
        device["metrics"] = metrics
        if battery is not None:
            device["battery"] = battery
        device["lastSync"] = datetime.now(timezone.utc).isoformat()
        self.save(device_id, device)
        return device


# Singleton
iot_devices_db = IoTDevicesDB()
