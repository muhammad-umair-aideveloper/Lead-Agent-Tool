"""
Dashboard / Analytics API endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import DashboardData, DashboardKPIs
from app.services.analytics import (
    get_full_dashboard,
    get_dashboard_kpis,
    get_intent_breakdown,
    get_state_distribution,
    get_source_distribution,
    get_daily_message_counts,
)

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardData)
async def dashboard(db: AsyncSession = Depends(get_db)):
    """Aggregated dashboard data."""
    return await get_full_dashboard(db)


@router.get("/kpis", response_model=DashboardKPIs)
async def kpis(db: AsyncSession = Depends(get_db)):
    """Top-line KPIs only."""
    return await get_dashboard_kpis(db)
