"""
Krishi Sewa CMS REST Endpoints
Provides full administrative CRUD operations for:
- Farmer Registrations & Records
- IoT Station Thresholds & Actuators
- Knowledge Base Articles & Vector Index Rebuilding
- Mandi Market Commodity Pricing
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException, BackgroundTasks

from config import settings
from db.farmers import farmer_db
from db import iot_db
from db.knowledge import knowledge_db
from db.market_prices import market_db
from data.seed_knowledge import seed_and_index_knowledge

router = APIRouter(prefix="/api/cms", tags=["cms"])


# ─────────────────────────────────────────────────────────────
# 1. FARMER MANAGEMENT CMS ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.get("/farmers")
async def list_farmers(district: str | None = None):
    """List all registered farmers with optional district filtering."""
    farmers = farmer_db.list_farmers(district=district)
    return {"farmers": farmers, "count": len(farmers)}


@router.post("/farmers")
async def create_farmer(payload: dict[str, Any]):
    """Register a new farmer entry."""
    if not payload.get("full_name"):
        raise HTTPException(status_code=400, detail="Farmer full name is required.")
    farmer = farmer_db.save_farmer(payload)
    return {"status": "success", "farmer": farmer}


@router.get("/farmers/{farmer_id}")
async def get_farmer(farmer_id: str):
    """Get details of a specific farmer."""
    farmer = farmer_db.get_farmer(farmer_id)
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found.")
    return {"farmer": farmer}


@router.put("/farmers/{farmer_id}")
async def update_farmer(farmer_id: str, payload: dict[str, Any]):
    """Update farmer record details."""
    updated = farmer_db.update_farmer(farmer_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Farmer record not found.")
    return {"status": "success", "farmer": updated}


@router.delete("/farmers/{farmer_id}")
async def delete_farmer(farmer_id: str):
    """Delete or archive a farmer record."""
    success = farmer_db.delete_farmer(farmer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Farmer record not found.")
    return {"status": "success", "message": f"Farmer {farmer_id} deleted."}


# ─────────────────────────────────────────────────────────────
# 2. IOT DEVICE & ACTUATOR CONTROL CMS ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.get("/iot/devices")
async def list_iot_devices():
    """List all registered IoT telemetry stations."""
    devices = iot_db.list_devices()
    return {"devices": devices, "count": len(devices)}


@router.post("/iot/devices")
async def register_iot_device(payload: dict[str, Any]):
    """Register a new IoT station configuration."""
    device_id = payload.get("device_id")
    name = payload.get("name")
    device_type = payload.get("device_type", "weather")
    if not device_id or not name:
        raise HTTPException(status_code=400, detail="device_id and name are required.")

    device = iot_db.register_device(
        device_id=device_id,
        name=name,
        device_type=device_type,
        location=payload.get("location", "main"),
        sensors=payload.get("sensors", []),
        actuators=payload.get("actuators", []),
        config=payload.get("config", {}),
        battery=payload.get("battery", 100),
        lat=payload.get("lat", 0.0),
        lng=payload.get("lng", 0.0),
    )
    return {"status": "success", "device": device}


@router.put("/iot/devices/{device_id}")
async def update_iot_device(device_id: str, payload: dict[str, Any]):
    """Update IoT station configuration, thresholds, or status."""
    if "sensors" in payload:
        payload["sensors_json"] = json.dumps(payload.pop("sensors"))
    if "actuators" in payload:
        payload["actuators_json"] = json.dumps(payload.pop("actuators"))
    if "config" in payload:
        payload["config_json"] = json.dumps(payload.pop("config"))

    updated = iot_db.update_device(device_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail=f"IoT Device {device_id} not found.")
    return {"status": "success", "device": updated}


@router.post("/iot/devices/{device_id}/actuator")
async def toggle_actuator(device_id: str, payload: dict[str, Any]):
    """Toggle digital actuator state (Irrigation Valve, Fan, Heater, Pump)."""
    actuator_name = payload.get("actuator")
    state = payload.get("state", "off")
    
    device = iot_db.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found.")

    config = json.loads(device.get("config_json") or "{}")
    actuators_state = config.get("actuators_state", {})
    actuators_state[actuator_name] = state
    config["actuators_state"] = actuators_state

    updated = iot_db.update_device(device_id, {"config_json": json.dumps(config)})
    return {
        "status": "success",
        "device_id": device_id,
        "actuator": actuator_name,
        "state": state,
        "updated_config": config,
    }


@router.delete("/iot/devices/{device_id}")
async def delete_iot_device(device_id: str):
    """Delete an IoT station configuration."""
    success = iot_db.delete_device(device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found.")
    return {"status": "success", "message": f"Device {device_id} deleted."}


# ─────────────────────────────────────────────────────────────
# 3. KNOWLEDGE BASE & RAG CMS ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.get("/knowledge")
async def list_knowledge_docs(category: str | None = None):
    """List all knowledge documents in database/knowledge/."""
    docs = knowledge_db.list_documents(category=category)
    stats = knowledge_db.get_stats()
    return {"documents": docs, "stats": stats}


@router.get("/knowledge/{category}/{doc_id}")
async def get_knowledge_doc(category: str, doc_id: str):
    """Get content of a Markdown knowledge file."""
    content = knowledge_db.get_document(category, doc_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Knowledge article not found.")
    return {"id": doc_id, "category": category, "content": content}


@router.post("/knowledge")
async def save_knowledge_doc(payload: dict[str, Any]):
    """Create or update a Markdown knowledge file."""
    doc_id = payload.get("id")
    category = payload.get("category", "guides")
    content = payload.get("content", "")

    if not doc_id or not content:
        raise HTTPException(status_code=400, detail="id and content are required.")

    valid_cats = ["diseases", "practices", "guides"]
    if category not in valid_cats:
        category = "guides"

    target_dir = Path(settings.database_root) / "knowledge" / category
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{doc_id}.md"

    target_path.write_text(content, encoding="utf-8")
    return {"status": "success", "id": doc_id, "category": category, "path": str(target_path)}


@router.delete("/knowledge/{category}/{doc_id}")
async def delete_knowledge_doc(category: str, doc_id: str):
    """Delete a Markdown knowledge file."""
    target_path = Path(settings.database_root) / "knowledge" / category / f"{doc_id}.md"
    if target_path.exists():
        target_path.unlink()
        return {"status": "success", "message": f"Deleted {doc_id}.md"}
    raise HTTPException(status_code=404, detail="File not found.")


@router.post("/knowledge/reindex")
async def reindex_knowledge_rag():
    """Trigger vector index rebuild for RAG knowledge search."""
    try:
        indexed_count = await seed_and_index_knowledge()
        return {"status": "success", "message": "Knowledge RAG vector index rebuilt", "indexed_chunks": indexed_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reindexing failed: {e}")


# ─────────────────────────────────────────────────────────────
# 4. MARKET PRICE CMS ENDPOINTS
# ─────────────────────────────────────────────────────────────

@router.get("/market")
async def list_market_prices(crop: str | None = None):
    """List mandi commodity price records."""
    prices = market_db.get_latest_prices(crop=crop)
    listings = market_db.get_listings(crop=crop)
    return {"prices": prices, "listings": listings, "count": len(prices) + len(listings)}


@router.post("/market")
async def create_market_price(payload: dict[str, Any]):
    """Add a new commodity market price rate or farmer listing."""
    is_listing = payload.get("is_listing", False)
    if is_listing:
        record = market_db.create_listing(payload)
    else:
        record = market_db.save_price(payload)
    return {"status": "success", "record": record}


@router.put("/market/{record_id}")
async def update_market_price(record_id: str, payload: dict[str, Any]):
    """Update a market price rate record."""
    existing = market_db.get(record_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Market price record not found.")
    existing.update(payload)
    market_db.save(record_id, existing)
    return {"status": "success", "record": existing}


@router.delete("/market/{record_id}")
async def delete_market_price(record_id: str):
    """Delete a market price record."""
    success = market_db.delete(record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Market record not found.")
    return {"status": "success", "message": f"Market record {record_id} deleted."}
