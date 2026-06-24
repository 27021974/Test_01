"""FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import events, jobs, sources, stats
from app.config import settings
from app.database import init_db
from app.jobs.fetch_all import run_fetch_all

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initialising database …")
    await init_db()

    # Seed source rows on first run
    await _seed_sources()

    # Schedule daily fetch
    scheduler.add_job(
        run_fetch_all,
        "cron",
        hour=settings.scheduler_hour,
        minute=0,
        id="daily_fetch",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started (daily fetch at %02d:00 UTC)", settings.scheduler_hour)

    yield

    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped.")


async def _seed_sources() -> None:
    """Ensure source rows exist in the DB (idempotent)."""
    from app.jobs.fetch_all import ADAPTERS, AsyncSessionLocal, _ensure_source
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSessionLocal() as session:
        async with session.begin():
            for adapter in ADAPTERS:
                await _ensure_source(session, adapter)


app = FastAPI(
    title=settings.app_name,
    description="MVP WebApp für Marktbeobachtung mit Insolvenz-Monitoring",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events.router)
app.include_router(sources.router)
app.include_router(jobs.router)
app.include_router(stats.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
