"""
Lead Reactivation Agent — FastAPI Application
───────────────────────────────────────────────
Entry point for the backend API server.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.logging_config import setup_logging
from app.routers import leads, webhooks, dashboard, config
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    setup_logging()
    await init_db()
    start_scheduler()
    yield  # Application runs here
    stop_scheduler()


app = FastAPI(
    title="Lead Reactivation Agent API",
    description="Autonomous AI-driven lead reactivation system powered by Gemini & Twilio",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────
app.include_router(leads.router)
app.include_router(webhooks.router)
app.include_router(dashboard.router)
app.include_router(config.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name}
