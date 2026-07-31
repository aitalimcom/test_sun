"""Pydantic models for IoT API."""
from pydantic import BaseModel
from typing import Any


class DeviceRegisterRequest(BaseModel):
    name: str
    device_type: str
    location: str = "main"
    sensors: list[str] = []
    actuators: list[str] = []
    config: dict[str, Any] = {}
    battery: int = 100
    lat: float = 0.0
    lng: float = 0.0


class DeviceUpdateRequest(BaseModel):
    name: str | None = None
    location: str | None = None
    status: str | None = None
    config: dict[str, Any] | None = None


class TelemetryData(BaseModel):
    data: dict[str, float]


class IoTActionRequest(BaseModel):
    device_id: str
    action: str
    params: dict[str, Any] = {}


class AlertCreateRequest(BaseModel):
    device_id: str
    metric: str
    value: float
    threshold: str
    severity: str = "warning"
    message: str = ""


class ScheduleCreateRequest(BaseModel):
    device_id: str
    action: str
    params: dict[str, Any] = {}
    cron_expr: str


class ChatMessage(BaseModel):
    message: str
    history: list[dict[str, str]] = []


class ChatResponse(BaseModel):
    reply: str
    device_config: dict[str, Any] | None = None
    esp32_code: str | None = None
    actions: list[dict[str, Any]] = []


class CronJobUpdate(BaseModel):
    enabled: bool
