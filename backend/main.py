import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routes import chat, doctor, market, weather, knowledge, admin, calendar, daily, feedback, ocr
from routes import iot, iot_chat, iot_cron

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("krishimitra")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("KrishiMitra backend initializing...")

    # 1. Initialize multi-agent graph
    from agents.registry import initialize_graph
    try:
        initialize_graph()
        logger.info("Multi-agent graph initialized")
    except Exception as e:
        logger.error(f"Failed to initialize agent graph: {e}")

    # 2. Seed database
    try:
        from data.market_mock import seed_market_prices
        from data.weather_mock import seed_weather_history
        from data.seed_knowledge import seed_and_index_knowledge
        from db.iot_db import seed_weather_device

        seed_market_prices()
        seed_weather_history()
        await seed_and_index_knowledge()
        seed_weather_device()
        logger.info("Database seeded including weather device")
    except Exception as e:
        logger.warning(f"Seeding skipped: {e}")

    # 3. Setup cron scheduler
    try:
        from core.cron import setup_default_jobs, cron_scheduler
        setup_default_jobs()
        await cron_scheduler.start()
        logger.info("Cron scheduler started")
    except Exception as e:
        logger.error(f"Failed to start cron scheduler: {e}")

    logger.info("KrishiMitra backend ready")
    yield

    try:
        from core.cron import cron_scheduler
        await cron_scheduler.stop()
    except Exception:
        pass
    logger.info("KrishiMitra backend shutting down")


app = FastAPI(
    title="Krishi Sewa API",
    description="Krishi Sewa — Government Agriculture Admin Panel and Farmer Assistant API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include Routers ──
app.include_router(chat.router)
app.include_router(doctor.router)
app.include_router(market.router)
app.include_router(weather.router)
app.include_router(knowledge.router)
app.include_router(admin.router)
app.include_router(calendar.router)
app.include_router(daily.router)
app.include_router(feedback.router)
app.include_router(ocr.router)

# ── IoT Routers ──
app.include_router(iot.router)
app.include_router(iot_chat.router)
app.include_router(iot_cron.router)


@app.get("/api/status")
async def status():
    return {
        "status": "ok",
        "service": "krishi-sewa",
        "version": "2.0.0",
    }
