"""
Fantasy HQ v2 — Python/FastAPI Backend
Independent scoring engine using FBref, Understat, FPL API.
No Fantrax private API required.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from routers import players, fixtures, alerts, waiver, fpl_proxy
from services.fixture_manager import fetch_and_store_fixtures, load_fixtures
from services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

CURRENT_SEASON = os.getenv("CURRENT_SEASON", "2025-26")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Fantasy HQ v2 starting...")

    if not load_fixtures(CURRENT_SEASON):
        logger.info(f"📅 Fetching fixtures for {CURRENT_SEASON}...")
        try:
            await fetch_and_store_fixtures(CURRENT_SEASON)
            logger.info("📅 Fixtures loaded successfully")
        except Exception as e:
            logger.warning(f"Could not pre-load fixtures: {e}")
    else:
        logger.info(f"📅 Fixtures for {CURRENT_SEASON} already stored")

    await start_scheduler()
    logger.info("✅ Ready — all services connected.")
    yield
    logger.info("🛑 Shutting down...")
    await stop_scheduler()


app = FastAPI(
    title="Fantasy HQ API",
    description="Fantasy football scoring engine — FBref + Understat + FPL",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def serve_dashboard():
    return FileResponse("static/index.html")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(players.router,  prefix="/api/players",  tags=["Players"])
app.include_router(fixtures.router, prefix="/api/fixtures", tags=["Fixtures"])
app.include_router(alerts.router,   prefix="/api/alerts",   tags=["Alerts"])
app.include_router(waiver.router,   prefix="/api/waiver",   tags=["Waiver"])
app.include_router(fpl_proxy.router)


@app.get("/api/health")
async def health():
    from services.fixture_manager import get_available_seasons
    return {
        "status":         "ok",
        "version":        "2.0.0",
        "current_season": CURRENT_SEASON,
        "stored_seasons": get_available_seasons(),
        "scoring_engine": "active",
    }