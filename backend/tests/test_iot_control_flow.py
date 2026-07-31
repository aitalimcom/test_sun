"""
Automated unit test suite for Dynamic IoT Device Routing & Control Chat Actuator Engine.
"""

from fastapi.testclient import TestClient
from main import app
from db import iot_db

client = TestClient(app)


def test_dynamic_device_creation_and_actuator_control():
    """Test creating a dynamic device, executing control chat, and updating actuators & alerts."""
    device_id = "test-polyhouse-99"

    # 1. Register new dynamic device
    device = iot_db.register_device(
        device_id=device_id,
        name="Polyhouse Beta",
        device_type="greenhouse",
        location="Pokhara Farm",
        sensors=["temperature", "moisture", "humidity"],
        actuators=["pump", "fan", "valve"],
    )
    assert device["device_id"] == device_id

    # 2. Execute Actuator Control via REST API
    actuator_res = client.post(
        f"/api/cms/iot/devices/{device_id}/actuator",
        json={"actuator": "pump", "state": "on"}
    )
    assert actuator_res.status_code == 200
    assert actuator_res.json()["state"] == "on"

    # 3. Verify device state updated in DB
    updated = iot_db.get_device(device_id)
    assert updated is not None
    import json
    config = json.loads(updated.get("config_json", "{}"))
    assert config.get("actuators_state", {}).get("pump") == "on"

    # 4. Create Active Alert
    alert = iot_db.create_alert(
        device_id=device_id,
        metric="temperature",
        value=39.5,
        threshold=">35.0",
        severity="warning",
        message="High temperature warning in Polyhouse Beta",
    )
    assert alert["device_id"] == device_id
    assert alert["status"] == "active"

    # 5. Clean up test device
    iot_db.delete_device(device_id)
