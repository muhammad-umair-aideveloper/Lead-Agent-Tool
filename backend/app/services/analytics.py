"""
Analytics Service
──────────────────
Aggregation queries for the dashboard.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import case, cast, func, select, Float
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, LeadState, Message, IntentCategory


async def get_dashboard_kpis(db: AsyncSession) -> dict:
    """Compute top-line KPIs."""
    total_leads = (await db.execute(select(func.count(Lead.id)))).scalar() or 0

    total_sent = (
        await db.execute(
            select(func.count(Message.id)).where(Message.direction == "outbound")
        )
    ).scalar() or 0

    total_replies = (
        await db.execute(
            select(func.count(Lead.id)).where(Lead.state == LeadState.replied)
        )
    ).scalar() or 0

    total_ignored = (
        await db.execute(
            select(func.count(Lead.id)).where(Lead.state == LeadState.ignored)
        )
    ).scalar() or 0

    total_opted_out = (
        await db.execute(
            select(func.count(Lead.id)).where(Lead.state == LeadState.opted_out)
        )
    ).scalar() or 0

    denominator = total_sent or 1
    reply_rate = round(total_replies / denominator * 100, 2)
    ignored_rate = round(total_ignored / denominator * 100, 2)

    # Average reply time (minutes)
    avg_reply_time = None
    reply_msgs = (
        await db.execute(
            select(Message)
            .where(Message.direction == "inbound")
            .where(Message.received_at.isnot(None))
        )
    ).scalars().all()

    if reply_msgs:
        deltas = []
        for rm in reply_msgs:
            # Find the last outbound message to this lead before this reply
            outbound = (
                await db.execute(
                    select(Message)
                    .where(Message.lead_id == rm.lead_id)
                    .where(Message.direction == "outbound")
                    .where(Message.sent_at < rm.received_at)
                    .order_by(Message.sent_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()

            if outbound and outbound.sent_at and rm.received_at:
                delta = (rm.received_at - outbound.sent_at).total_seconds() / 60
                deltas.append(delta)

        if deltas:
            avg_reply_time = round(sum(deltas) / len(deltas), 1)

    return {
        "total_leads": total_leads,
        "total_messages_sent": total_sent,
        "total_replies": total_replies,
        "total_ignored": total_ignored,
        "total_opted_out": total_opted_out,
        "reply_rate": reply_rate,
        "ignored_rate": ignored_rate,
        "avg_reply_time_minutes": avg_reply_time,
    }


async def get_intent_breakdown(db: AsyncSession) -> List[dict]:
    """Return reply rates per intent category."""
    results = []
    for intent in IntentCategory:
        total = (
            await db.execute(
                select(func.count(Lead.id)).where(Lead.intent_category == intent)
            )
        ).scalar() or 0

        replied = (
            await db.execute(
                select(func.count(Lead.id))
                .where(Lead.intent_category == intent)
                .where(Lead.state == LeadState.replied)
            )
        ).scalar() or 0

        results.append({
            "intent_category": intent.value,
            "count": total,
            "reply_count": replied,
            "reply_rate": round(replied / max(total, 1) * 100, 2),
        })
    return results


async def get_state_distribution(db: AsyncSession) -> Dict[str, int]:
    """Count of leads per state."""
    dist = {}
    for state in LeadState:
        count = (
            await db.execute(
                select(func.count(Lead.id)).where(Lead.state == state)
            )
        ).scalar() or 0
        dist[state.value] = count
    return dist


async def get_source_distribution(db: AsyncSession) -> Dict[str, int]:
    """Count of leads per source."""
    rows = (
        await db.execute(
            select(Lead.lead_source, func.count(Lead.id))
            .group_by(Lead.lead_source)
        )
    ).all()
    return {row[0]: row[1] for row in rows}


async def get_daily_message_counts(db: AsyncSession, days: int = 30) -> List[dict]:
    """Messages sent per day for the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = (
        await db.execute(
            select(
                func.date(Message.sent_at).label("date"),
                func.count(Message.id).label("count"),
            )
            .where(Message.direction == "outbound")
            .where(Message.sent_at >= cutoff)
            .group_by(func.date(Message.sent_at))
            .order_by(func.date(Message.sent_at))
        )
    ).all()
    return [{"date": str(row[0]), "count": row[1]} for row in rows]


async def get_full_dashboard(db: AsyncSession) -> dict:
    """Aggregate all dashboard data in one call."""
    return {
        "kpis": await get_dashboard_kpis(db),
        "intent_breakdown": await get_intent_breakdown(db),
        "state_distribution": await get_state_distribution(db),
        "source_distribution": await get_source_distribution(db),
        "daily_messages": await get_daily_message_counts(db),
    }
