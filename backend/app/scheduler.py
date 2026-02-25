"""
Background Scheduler
─────────────────────
Runs periodic tasks: timeout checks, deferred message dispatch.
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.database import async_session_factory
from app.logging_config import logger
from app.services.state_machine import check_ignored_leads

scheduler = AsyncIOScheduler()


async def _run_timeout_check():
    """Periodic task: mark stale message_sent leads as ignored."""
    async with async_session_factory() as session:
        try:
            count = await check_ignored_leads(session)
            await session.commit()
            if count > 0:
                await logger.ainfo("scheduler_timeout_check", marked_ignored=count)
        except Exception as exc:
            await logger.aerror("scheduler_timeout_check_error", error=str(exc))
            await session.rollback()


def start_scheduler():
    """Register and start all periodic tasks."""
    scheduler.add_job(
        _run_timeout_check,
        trigger=IntervalTrigger(minutes=30),
        id="timeout_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("scheduler_started")


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")
