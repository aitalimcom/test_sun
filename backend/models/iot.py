from pydantic import BaseModel
from typing import Any, List, Optional


class IoTDeviceMetric(BaseModel):
    label: str
    label_np: str
    value: str
    unit: str


class IoTDevice(BaseModel):
    id: str
    name: str
    name_np: str
    status: str
    deviceType: str
    battery: int
    metrics: List[IoTDeviceMetric]
    landId: str = "land-1"
    lastSync: str


class IoTActionRequest(BaseModel):
    device_id: str
    action: str  # e.g., "toggle_valve", "irrigate_1m"
    value: Optional[Any] = None
