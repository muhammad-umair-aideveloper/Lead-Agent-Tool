"""
Configuration management API endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import AppConfigOut, AppConfigUpdate

router = APIRouter(prefix="/api/v1/config", tags=["config"])


@router.get("/", response_model=AppConfigOut)
async def get_config():
    """Return current application configuration (non-sensitive)."""
    return AppConfigOut(
        business_hours_start=settings.business_hours_start,
        business_hours_end=settings.business_hours_end,
        business_hours_timezone=settings.business_hours_timezone,
        default_sms_tone=settings.default_sms_tone,
        ignore_timeout_hours=settings.ignore_timeout_hours,
        max_retries=settings.max_retries,
    )


@router.put("/", response_model=AppConfigOut)
async def update_config(payload: AppConfigUpdate):
    """
    Update runtime configuration.
    Note: In production this would persist to a DB or config store.
    For this implementation, it updates the in-memory settings.
    """
    if payload.business_hours_start is not None:
        settings.business_hours_start = payload.business_hours_start
    if payload.business_hours_end is not None:
        settings.business_hours_end = payload.business_hours_end
    if payload.business_hours_timezone is not None:
        settings.business_hours_timezone = payload.business_hours_timezone
    if payload.default_sms_tone is not None:
        settings.default_sms_tone = payload.default_sms_tone
    if payload.ignore_timeout_hours is not None:
        settings.ignore_timeout_hours = payload.ignore_timeout_hours
    if payload.max_retries is not None:
        settings.max_retries = payload.max_retries

    return AppConfigOut(
        business_hours_start=settings.business_hours_start,
        business_hours_end=settings.business_hours_end,
        business_hours_timezone=settings.business_hours_timezone,
        default_sms_tone=settings.default_sms_tone,
        ignore_timeout_hours=settings.ignore_timeout_hours,
        max_retries=settings.max_retries,
    )
