"""
Automated empirical test suite for Krishi Sewa CMS REST Endpoints.
Tests CRUD operations for Farmers, IoT Devices, Knowledge Base, and Market Prices.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_status_endpoint():
    """Verify backend system status."""
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "krishi-sewa"


def test_farmer_crud_workflow():
    """Test creating, listing, updating, and deleting a farmer record."""
    new_farmer = {
        "full_name": "रामबहादुर श्रेष्ठ",
        "citizenship_no": "27-01-79-12345",
        "phone": "9841000000",
        "district": "चितवन",
        "palika": "भरतपुर महानगरपालिका",
        "ward": "10",
        "land_size_ropani": 5.5,
        "land_size_bigha": 0.41,
        "crops": ["धान", "मकै"],
    }
    
    # 1. Create Farmer
    post_res = client.post("/api/cms/farmers", json=new_farmer)
    assert post_res.status_code == 200
    created = post_res.json()["farmer"]
    assert created["full_name"] == "रामबहादुर श्रेष्ठ"
    farmer_id = created["id"]

    # 2. Get Farmer
    get_res = client.get(f"/api/cms/farmers/{farmer_id}")
    assert get_res.status_code == 200
    assert get_res.json()["farmer"]["citizenship_no"] == "27-01-79-12345"

    # 3. List Farmers
    list_res = client.get("/api/cms/farmers")
    assert list_res.status_code == 200
    assert list_res.json()["count"] >= 1

    # 4. Update Farmer
    put_res = client.put(f"/api/cms/farmers/{farmer_id}", json={"land_size_ropani": 7.0})
    assert put_res.status_code == 200
    assert put_res.json()["farmer"]["land_size_ropani"] == 7.0

    # 5. Delete Farmer
    del_res = client.delete(f"/api/cms/farmers/{farmer_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"


def test_iot_device_crud_workflow():
    """Test IoT station creation, threshold updates, and actuator toggles."""
    device_data = {
        "device_id": "test-greenhouse-01",
        "name": "Greenhouse Alpha",
        "device_type": "greenhouse",
        "location": "Kirtipur Farm",
        "sensors": ["temperature", "soil_moisture", "humidity"],
        "actuators": ["irrigation_valve", "ventilation_fan"],
    }

    # 1. Register Device
    post_res = client.post("/api/cms/iot/devices", json=device_data)
    assert post_res.status_code == 200
    assert post_res.json()["device"]["device_id"] == "test-greenhouse-01"

    # 2. Toggle Actuator
    actuator_res = client.post(
        "/api/cms/iot/devices/test-greenhouse-01/actuator",
        json={"actuator": "irrigation_valve", "state": "on"}
    )
    assert actuator_res.status_code == 200
    assert actuator_res.json()["state"] == "on"

    # 3. Delete Device
    del_res = client.delete("/api/cms/iot/devices/test-greenhouse-01")
    assert del_res.status_code == 200


def test_knowledge_base_crud():
    """Test knowledge article creation, retrieving, and deleting."""
    article_data = {
        "id": "test_crop_guide",
        "category": "guides",
        "content": "# Rice Cultivation Guide\n\nTips for high yield rice in Terai region."
    }

    # 1. Save Document
    save_res = client.post("/api/cms/knowledge", json=article_data)
    assert save_res.status_code == 200

    # 2. Retrieve Document
    get_res = client.get("/api/cms/knowledge/guides/test_crop_guide")
    assert get_res.status_code == 200
    assert "# Rice Cultivation Guide" in get_res.json()["content"]

    # 3. Delete Document
    del_res = client.delete("/api/cms/knowledge/guides/test_crop_guide")
    assert del_res.status_code == 200


def test_market_price_crud():
    """Test market price listing creation and deletion."""
    market_data = {
        "id": "test_mandi_potato",
        "crop": "Potato (आलु)",
        "price_per_kg": 45.0,
        "market_location": "Kalimati Mandi",
    }

    # 1. Create Price Entry
    create_res = client.post("/api/cms/market", json=market_data)
    assert create_res.status_code == 200

    # 2. List Prices
    list_res = client.get("/api/cms/market?crop=Potato")
    assert list_res.status_code == 200

    # 3. Delete Entry
    del_res = client.delete("/api/cms/market/test_mandi_potato")
    assert del_res.status_code == 200
