"""
Lead State Machine
───────────────────
Manages lead lifecycle transitions and the autonomous processing orchestrator.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.logging_config import logger
from app.models.lead import Batch, Lead, LeadState, Message, SmsTone
from app.services.ai_reasoning import analyze_lead
from app.services.twilio_sms import send_sms


# ── State transitions ────────────────────────────────────────────

VALID_TRANSITIONS = {
    LeadState.pending: {LeadState.message_sent},
    LeadState.message_sent: {LeadState.replied, LeadState.ignored, LeadState.opted_out},
    LeadState.replied: {LeadState.message_sent},  # Allow follow-up
    LeadState.ignored: {LeadState.message_sent},   # Allow retry
    LeadState.opted_out: set(),                     # Terminal state
}


async def transition_lead(
    db: AsyncSession, lead: Lead, new_state: LeadState
) -> Lead:
    """Transition a lead to a new state if the transition is valid."""
    if new_state not in VALID_TRANSITIONS.get(lead.state, set()):
        await logger.awarn(
            "invalid_state_transition",
            lead_id=lead.lead_id,
            current=lead.state,
            requested=new_state,
        )
        raise ValueError(
            f"Cannot transition from {lead.state} to {new_state}"
        )

    old_state = lead.state
    lead.state = new_state
    lead.updated_at = datetime.utcnow()
    await db.flush()

    await logger.ainfo(
        "lead_state_changed",
        lead_id=lead.lead_id,
        old_state=old_state,
        new_state=new_state,
    )
    return lead


# ── Autonomous orchestrator ──────────────────────────────────────


async def process_pending_leads(db: AsyncSession, batch_id: str | None = None) -> dict:
    """
    Core autonomous workflow:
    1. Fetch all pending leads (optionally for a specific batch).
    2. Run AI reasoning on each.
    3. Send SMS for high/medium/low intent leads.
    4. Transition states accordingly.
    """
    query = select(Lead).where(Lead.state == LeadState.pending)
    if batch_id:
        query = query.where(Lead.batch_id == batch_id)

    result = await db.execute(query)
    leads: List[Lead] = list(result.scalars().all())

    stats = {"total": len(leads), "analyzed": 0, "sent": 0, "skipped": 0, "errors": 0}

    await logger.ainfo("processing_batch_start", batch_id=batch_id, lead_count=len(leads))

    for lead in leads:
        try:
            # ── Step 1: AI Analysis ──
            ai_result = await analyze_lead(
                full_name=lead.full_name,
                phone_number=lead.phone_number,
                last_interaction_date=str(lead.last_interaction_date),
                lead_source=lead.lead_source,
                notes=lead.notes,
                tone_preference=settings.default_sms_tone,
            )

            # Persist AI enrichment
            lead.intent_category = IntentCategory(ai_result["intent_category"])
            lead.intent_rationale = ai_result["intent_rationale"]
            lead.recommended_angle = ai_result["recommended_sms"]
            lead.sms_tone = SmsTone(ai_result.get("sms_tone", settings.default_sms_tone))
            stats["analyzed"] += 1

            # ── Step 2: Decide whether to send ──
            if ai_result["intent_category"] == "Not Interested":
                await logger.ainfo("lead_skipped_not_interested", lead_id=lead.lead_id)
                stats["skipped"] += 1
                continue

            # ── Step 3: Send SMS ──
            sms_result = await send_sms(
                to_number=lead.phone_number,
                body=ai_result["recommended_sms"],
                intent_score=ai_result["intent_category"],
                message_variant=f"batch-{batch_id or 'manual'}",
            )

            if sms_result.get("status") == "deferred":
                # Will be retried later during business hours
                stats["skipped"] += 1
                continue

            # ── Step 4: Record message ──
            msg = Message(
                lead_id=lead.lead_id,
                direction="outbound",
                body=ai_result["recommended_sms"],
                twilio_sid=sms_result.get("twilio_sid"),
                twilio_status=sms_result.get("status"),
                intent_score=ai_result["intent_category"],
                message_variant=f"batch-{batch_id or 'manual'}",
                sms_tone=lead.sms_tone,
                sent_at=sms_result.get("sent_at"),
            )
            db.add(msg)

            # ── Step 5: Transition state ──
            await transition_lead(db, lead, LeadState.message_sent)
            stats["sent"] += 1

        except Exception as exc:
            stats["errors"] += 1
            await logger.aerror(
                "lead_processing_error",
                lead_id=lead.lead_id,
                error=str(exc),
            )
            continue

    # Update batch status
    if batch_id:
        batch_result = await db.execute(select(Batch).where(Batch.batch_id == batch_id))
        batch = batch_result.scalar_one_or_none()
        if batch:
            batch.status = "completed"
            batch.completed_at = datetime.utcnow()
            batch.processed_leads = stats["analyzed"]

    await db.flush()

    await logger.ainfo("processing_batch_complete", batch_id=batch_id, stats=stats)
    return stats


# ── Timeout checker ──────────────────────────────────────────────


async def check_ignored_leads(db: AsyncSession) -> int:
    """
    Mark leads as 'ignored' if they were sent a message but haven't
    replied within the configured timeout.
    """
    cutoff = datetime.utcnow() - timedelta(hours=settings.ignore_timeout_hours)

    # Find leads that were messaged before cutoff and are still in message_sent
    result = await db.execute(
        select(Lead)
        .where(Lead.state == LeadState.message_sent)
        .where(Lead.updated_at < cutoff)
    )
    stale_leads = list(result.scalars().all())

    count = 0
    for lead in stale_leads:
        try:
            await transition_lead(db, lead, LeadState.ignored)
            count += 1
        except ValueError:
            pass

    await logger.ainfo("ignored_check_complete", marked_ignored=count)
    return count


# ── Inbound reply handler ────────────────────────────────────────


async def handle_inbound_reply(
    db: AsyncSession,
    from_number: str,
    body: str,
    twilio_sid: str,
) -> dict:
    """
    Process an inbound SMS reply:
    - Find the matching lead by phone number.
    - Record the message.
    - Transition state (replied or opted_out).
    """
    from app.services.twilio_sms import is_opt_out

    result = await db.execute(
        select(Lead).where(Lead.phone_number == from_number)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        await logger.awarn("inbound_sms_unknown_number", from_number=from_number)
        return {"status": "unknown_number", "lead_id": None}

    # Record message
    msg = Message(
        lead_id=lead.lead_id,
        direction="inbound",
        body=body,
        twilio_sid=twilio_sid,
        received_at=datetime.utcnow(),
    )
    db.add(msg)

    # Determine new state
    if is_opt_out(body):
        new_state = LeadState.opted_out
    else:
        new_state = LeadState.replied

    try:
        await transition_lead(db, lead, new_state)
    except ValueError:
        await logger.awarn(
            "inbound_transition_failed",
            lead_id=lead.lead_id,
            current_state=lead.state,
            attempted=new_state,
        )

    await db.flush()

    return {
        "status": "processed",
        "lead_id": lead.lead_id,
        "new_state": lead.state.value,
    }
