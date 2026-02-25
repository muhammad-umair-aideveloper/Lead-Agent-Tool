"""
Lead management API endpoints.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.lead import Lead, LeadState, Batch, Message
from app.models.schemas import (
    LeadOut,
    LeadListOut,
    MessageOut,
    BatchOut,
)
from app.services.ingestion import validate_csv, ingest_leads
from app.services.state_machine import process_pending_leads

router = APIRouter(prefix="/api/v1/leads", tags=["leads"])


# ── List batches (MUST be before /{lead_id} to avoid path capture) ──


@router.get("/batches/list", response_model=list[BatchOut])
async def list_batches(db: AsyncSession = Depends(get_db)):
    """List all processing batches."""
    result = await db.execute(select(Batch).order_by(Batch.created_at.desc()))
    return result.scalars().all()


# ── Export leads as CSV (MUST be before /{lead_id}) ──────────────


@router.get("/export/csv")
async def export_leads_csv(
    state: Optional[str] = None,
    intent: Optional[str] = None,
    source: Optional[str] = None,
    batch_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Export filtered leads as a downloadable CSV."""
    from fastapi.responses import StreamingResponse

    query = select(Lead)
    if state:
        query = query.where(Lead.state == state)
    if intent:
        query = query.where(Lead.intent_category == intent)
    if source:
        query = query.where(Lead.lead_source == source)
    if batch_id:
        query = query.where(Lead.batch_id == batch_id)

    result = await db.execute(query.order_by(Lead.created_at.desc()))
    leads = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "lead_id", "full_name", "phone_number", "email",
        "last_interaction_date", "lead_source", "notes",
        "intent_category", "intent_rationale", "recommended_angle",
        "sms_tone", "state", "batch_id", "created_at",
    ])

    for lead in leads:
        writer.writerow([
            lead.lead_id, lead.full_name, lead.phone_number, lead.email,
            lead.last_interaction_date, lead.lead_source, lead.notes,
            lead.intent_category.value if lead.intent_category else "",
            lead.intent_rationale, lead.recommended_angle,
            lead.sms_tone.value if lead.sms_tone else "",
            lead.state.value, lead.batch_id, lead.created_at,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
    )


# ── CSV Upload ───────────────────────────────────────────────────


@router.post("/upload", response_model=BatchOut)
async def upload_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a CSV file to create a new lead reactivation batch."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")

    try:
        df, warnings = await validate_csv(contents)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if df.empty:
        raise HTTPException(status_code=422, detail="No valid leads found after validation.")

    batch = await ingest_leads(df, db, filename=file.filename)
    await db.commit()
    return batch


# ── Process batch ────────────────────────────────────────────────


@router.post("/process/{batch_id}")
async def process_batch(
    batch_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Kick off autonomous processing for a batch."""
    batch_result = await db.execute(select(Batch).where(Batch.batch_id == batch_id))
    batch = batch_result.scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found.")

    stats = await process_pending_leads(db, batch_id=batch_id)
    await db.commit()

    return {"batch_id": batch_id, "stats": stats}


# ── List leads ───────────────────────────────────────────────────


@router.get("/", response_model=LeadListOut)
async def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    state: Optional[str] = None,
    intent: Optional[str] = None,
    source: Optional[str] = None,
    batch_id: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List leads with filtering and pagination."""
    query = select(Lead)

    if state:
        query = query.where(Lead.state == state)
    if intent:
        query = query.where(Lead.intent_category == intent)
    if source:
        query = query.where(Lead.lead_source == source)
    if batch_id:
        query = query.where(Lead.batch_id == batch_id)
    if search:
        query = query.where(
            or_(
                Lead.full_name.ilike(f"%{search}%"),
                Lead.lead_id.ilike(f"%{search}%"),
                Lead.phone_number.ilike(f"%{search}%"),
            )
        )
    if date_from:
        try:
            dt = datetime.fromisoformat(date_from)
            query = query.where(Lead.last_interaction_date >= dt)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to)
            query = query.where(Lead.last_interaction_date <= dt)
        except ValueError:
            pass

    # Count total
    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    # Paginate
    query = query.order_by(Lead.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    leads = result.scalars().all()

    return LeadListOut(
        leads=[LeadOut.model_validate(l) for l in leads],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Get single lead ─────────────────────────────────────────────


@router.get("/{lead_id}", response_model=LeadOut)
async def get_lead(lead_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single lead by lead_id."""
    result = await db.execute(select(Lead).where(Lead.lead_id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")
    return lead


# ── Get lead messages ────────────────────────────────────────────


@router.get("/{lead_id}/messages", response_model=list[MessageOut])
async def get_lead_messages(lead_id: str, db: AsyncSession = Depends(get_db)):
    """Get all messages for a specific lead."""
    result = await db.execute(
        select(Message)
        .where(Message.lead_id == lead_id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()



