"""
Seed Database — Populate sample data for hackathon demo
Run: python scripts/seed_database.py
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

DB_ROOT = Path(__file__).parent.parent / "database"


def seed_users():
    """Create demo user."""
    users_dir = DB_ROOT / "users"
    users_dir.mkdir(parents=True, exist_ok=True)

    demo_user = {
        "id": "demo-user-1",
        "name": "Demo Farmer (किसान)",
        "phone": "+977-98XXXXXXXX",
        "location": "Chitwan, Nepal",
        "language": "ne",
        "farm_ids": ["demo-farm-1"],
        "created_at": "2026-07-29T00:00:00",
    }

    with open(users_dir / "demo-user-1.json", "w", encoding="utf-8") as f:
        json.dump(demo_user, f, indent=2, ensure_ascii=False)

    print("✅ Seeded: 1 user")


def seed_farms():
    """Create demo farm."""
    farms_dir = DB_ROOT / "farms"
    farms_dir.mkdir(parents=True, exist_ok=True)

    demo_farm = {
        "id": "demo-farm-1",
        "name": "सुन्दर खेत",
        "owner": "Demo Farmer",
        "user_id": "demo-user-1",
        "location": "Chitwan, Nepal",
        "district": "Chitwan",
        "area_hectares": 2.5,
        "soil_type": "Alluvial",
        "irrigation_type": "canal",
        "crops": ["Rice", "Maize", "Lentil"],
        "created_at": "2026-07-29T00:00:00",
    }

    with open(farms_dir / "demo-farm-1.json", "w", encoding="utf-8") as f:
        json.dump(demo_farm, f, indent=2, ensure_ascii=False)

    print("✅ Seeded: 1 farm")


def seed_market_prices():
    """Create demo market price data."""
    prices_dir = DB_ROOT / "market_prices"
    prices_dir.mkdir(parents=True, exist_ok=True)

    prices = [
        {"id": "price-rice-basmati", "crop": "Rice (Basmati)", "price_per_kg": 85.0, "market": "Kalimati", "date": "2026-07-29", "trend": "up"},
        {"id": "price-rice-mansuli", "crop": "Rice (Mansuli)", "price_per_kg": 52.0, "market": "Kalimati", "date": "2026-07-29", "trend": "stable"},
        {"id": "price-wheat", "crop": "Wheat", "price_per_kg": 42.0, "market": "Birgunj", "date": "2026-07-29", "trend": "down"},
        {"id": "price-maize", "crop": "Maize", "price_per_kg": 35.0, "market": "Bharatpur", "date": "2026-07-29", "trend": "up"},
        {"id": "price-lentil", "crop": "Lentil", "price_per_kg": 130.0, "market": "Kalimati", "date": "2026-07-29", "trend": "stable"},
    ]

    for price in prices:
        with open(prices_dir / f"{price['id']}.json", "w", encoding="utf-8") as f:
            json.dump(price, f, indent=2, ensure_ascii=False)

    print(f"✅ Seeded: {len(prices)} market prices")


def main():
    print("🌾 Seeding KrishiMitra database...\n")
    seed_users()
    seed_farms()
    seed_market_prices()
    print("\n🎉 Database seeded successfully!")


if __name__ == "__main__":
    main()
