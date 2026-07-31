import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routes import chat, doctor, market, weather, knowledge, admin, iot, calendar, daily, feedback, ocr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("krishimitra")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI Application Lifespan — Initialize services on startup."""
    logger.info("🚀 KrishiMitra backend initializing...")

    # 1. Initialize multi-agent graph
    from agents.registry import initialize_graph
    try:
        initialize_graph()
        logger.info("✅ Multi-agent graph initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize agent graph: {e}")

    # 2. Seed mock files and database collections
    try:
        from data.market_mock import seed_market_prices
        from data.weather_mock import seed_weather_history
        from data.seed_knowledge import seed_and_index_knowledge
        
        logger.info("Seeding database price files...")
        seed_market_prices()
        
        logger.info("Seeding weather history CSV...")
        seed_weather_history()
        
        logger.info("Seeding local RAG wiki documents...")
        await seed_and_index_knowledge()
        
        logger.info("✅ Database and CSV indexing complete")
    except Exception as e:
        logger.warning(f"⚠️ Seeding database collections skipped: {e}")

    # 3. Setup cron scheduler
    try:
        from core.cron import setup_default_jobs, cron_scheduler
        setup_default_jobs()
        await cron_scheduler.start()
        logger.info("⏰ Background cron scheduler started")
    except Exception as e:
        logger.error(f"❌ Failed to start cron scheduler: {e}")

    logger.info("✅ KrishiMitra backend ready")
    yield
    
    # 4. Shutdown scheduler on stop
    try:
        from core.cron import cron_scheduler
        await cron_scheduler.stop()
        logger.info("👋 Background cron scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        
    logger.info("👋 KrishiMitra backend shutting down")


app = FastAPI(
    title="कृषि सेवा API",
    description="Krishi Sewa — Government Agriculture Admin Panel and Farmer Assistant API",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS Middleware ──
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
app.include_router(iot.router)
app.include_router(calendar.router)
app.include_router(daily.router)
app.include_router(feedback.router)
app.include_router(ocr.router)


@app.get("/api/status")
async def status():
    return {
        "status": "ok",
        "service": "krishi-sewa",
        "version": "0.1.0",
    }
