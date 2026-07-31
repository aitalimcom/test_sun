"""
IoT CSV database layer.
All IoT data is stored as CSV for tabular agent compatibility.
Float values prioritized for sensor readings.
"""
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from config import settings

IOT_DIR = settings.database_path / "iot"
DEVICES_CSV = IOT_DIR / "devices.csv"
ALERTS_CSV = IOT_DIR / "alerts.csv"
SCHEDULES_CSV = IOT_DIR / "schedules.csv"

DEVICES_HEADER = [
    "device_id", "name", "device_type", "location", "status",
    "battery", "lat", "lng", "sensors_json", "actuators_json",
    "config_json", "created_at"
]
ALERTS_HEADER = [
    "alert_id", "device_id", "metric", "value", "threshold",
    "severity", "status", "message", "created_at"
]
SCHEDULES_HEADER = [
    "schedule_id", "device_id", "action", "params_json",
    "cron_expr", "enabled", "created_at"
]


def _ensure_dir():
    IOT_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_csv(path: Path, header: list[str]):
    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(header)


def _read_all(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_all(path: Path, header: list[str], rows: list[dict]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def _append_row(path: Path, header: list[str], row: dict):
    exists = path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


# ── Devices ──

def list_devices() -> list[dict]:
    _ensure_dir()
    _ensure_csv(DEVICES_CSV, DEVICES_HEADER)
    return _read_all(DEVICES_CSV)


def get_device(device_id: str) -> dict | None:
    for d in list_devices():
        if d["device_id"] == device_id:
            return d
    return None


def register_device(
    device_id: str,
    name: str,
    device_type: str,
    location: str = "main",
    sensors: list[str] | None = None,
    actuators: list[str] | None = None,
    config: dict | None = None,
    battery: int = 100,
    lat: float = 0.0,
    lng: float = 0.0,
) -> dict:
    _ensure_dir()
    _ensure_csv(DEVICES_CSV, DEVICES_HEADER)
    now = datetime.now().isoformat()
    device = {
        "device_id": device_id,
        "name": name,
        "device_type": device_type,
        "location": location,
        "status": "active",
        "battery": str(battery),
        "lat": str(lat),
        "lng": str(lng),
        "sensors_json": json.dumps(sensors or []),
        "actuators_json": json.dumps(actuators or []),
        "config_json": json.dumps(config or {}),
        "created_at": now,
    }
    _append_row(DEVICES_CSV, DEVICES_HEADER, device)
    return device


def update_device(device_id: str, updates: dict) -> dict | None:
    devices = list_devices()
    for i, d in enumerate(devices):
        if d["device_id"] == device_id:
            devices[i].update(updates)
            _write_all(DEVICES_CSV, DEVICES_HEADER, devices)
            return devices[i]
    return None


def delete_device(device_id: str) -> bool:
    devices = list_devices()
    new = [d for d in devices if d["device_id"] != device_id]
    if len(new) < len(devices):
        _write_all(DEVICES_CSV, DEVICES_HEADER, new)
        return True
    return False


# ── Telemetry (per-device CSV) ──

def _telemetry_path(device_id: str) -> Path:
    return IOT_DIR / f"telemetry_{device_id}.csv"


def _telemetry_header(device_id: str) -> list[str]:
    device = get_device(device_id)
    sensors = json.loads(device["sensors_json"]) if device else []
    actuators = json.loads(device["actuators_json"]) if device else []
    return ["timestamp"] + sensors + actuators


def append_telemetry(device_id: str, data: dict):
    _ensure_dir()
    path = _telemetry_path(device_id)
    header = _telemetry_header(device_id)
    _ensure_csv(path, header)
    row = {"timestamp": datetime.now().isoformat()}
    row.update(data)
    _append_row(path, header, row)


def get_telemetry(device_id: str, limit: int = 100) -> list[dict]:
    path = _telemetry_path(device_id)
    if not path.exists():
        return []
    rows = _read_all(path)
    return rows[-limit:]


def get_latest_telemetry(device_id: str) -> dict | None:
    rows = get_telemetry(device_id, limit=1)
    return rows[0] if rows else None


def seed_weather_device():
    """Create default weather station device if not exists."""
    if get_device("weather-001"):
        return
    register_device(
        device_id="weather-001",
        name="Weather Station",
        device_type="weather",
        location="main",
        sensors=["temperature", "humidity", "co2"],
        actuators=[],
        battery=95,
    )
    # Seed some initial telemetry
    import random
    for _ in range(10):
        append_telemetry("weather-001", {
            "temperature": round(random.uniform(18.0, 35.0), 1),
            "humidity": round(random.uniform(30.0, 90.0), 1),
            "co2": round(random.uniform(350.0, 500.0), 1),
        })


# ── Alerts ──

def list_alerts(status: str | None = None) -> list[dict]:
    _ensure_dir()
    _ensure_csv(ALERTS_CSV, ALERTS_HEADER)
    alerts = _read_all(ALERTS_CSV)
    if status:
        alerts = [a for a in alerts if a["status"] == status]
    return alerts


def create_alert(
    device_id: str,
    metric: str,
    value: float,
    threshold: str,
    severity: str = "warning",
    message: str = "",
) -> dict:
    _ensure_dir()
    _ensure_csv(ALERTS_CSV, ALERTS_HEADER)
    alert_id = f"alert-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    alert = {
        "alert_id": alert_id,
        "device_id": device_id,
        "metric": metric,
        "value": str(value),
        "threshold": threshold,
        "severity": severity,
        "status": "active",
        "message": message,
        "created_at": datetime.now().isoformat(),
    }
    _append_row(ALERTS_CSV, ALERTS_HEADER, alert)
    return alert


def resolve_alert(alert_id: str) -> bool:
    alerts = list_alerts()
    for i, a in enumerate(alerts):
        if a["alert_id"] == alert_id:
            alerts[i]["status"] = "resolved"
            _write_all(ALERTS_CSV, ALERTS_HEADER, alerts)
            return True
    return False


# ── Schedules ──

def list_schedules(device_id: str | None = None) -> list[dict]:
    _ensure_dir()
    _ensure_csv(SCHEDULES_CSV, SCHEDULES_HEADER)
    schedules = _read_all(SCHEDULES_CSV)
    if device_id:
        schedules = [s for s in schedules if s["device_id"] == device_id]
    return schedules


def create_schedule(
    device_id: str,
    action: str,
    params: dict,
    cron_expr: str,
) -> dict:
    _ensure_dir()
    _ensure_csv(SCHEDULES_CSV, SCHEDULES_HEADER)
    schedule_id = f"sch-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    schedule = {
        "schedule_id": schedule_id,
        "device_id": device_id,
        "action": action,
        "params_json": json.dumps(params),
        "cron_expr": cron_expr,
        "enabled": "true",
        "created_at": datetime.now().isoformat(),
    }
    _append_row(SCHEDULES_CSV, SCHEDULES_HEADER, schedule)
    return schedule


def delete_schedule(schedule_id: str) -> bool:
    schedules = list_schedules()
    new = [s for s in schedules if s["schedule_id"] != schedule_id]
    if len(new) < len(schedules):
        _write_all(SCHEDULES_CSV, SCHEDULES_HEADER, new)
        return True
    return False
