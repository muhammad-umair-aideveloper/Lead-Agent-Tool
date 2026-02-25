"""
Data Ingestion Pipeline
─────────────────────────
Validates, cleans, normalises and persists CSV lead data.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from io import StringIO
from typing import List, Tuple

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import logger
from app.models.lead import Batch, Lead, LeadState


# ── Helpers ──────────────────────────────────────────────────────

REQUIRED_COLUMNS = {
    "lead_id",
    "full_name",
    "phone_number",
    "last_interaction_date",
    "lead_source",
}

OPTIONAL_COLUMNS = {"email", "notes"}

PHONE_RE = re.compile(r"^\+?[1-9]\d{6,14}$")


def _normalise_phone(raw: str) -> str:
    """Strip non-digits except leading '+' and validate E.164-ish format."""
    cleaned = re.sub(r"[\s\-\(\).]", "", str(raw).strip())
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    if not PHONE_RE.match(cleaned.replace("+", "")):
        raise ValueError(f"Invalid phone number: {raw}")
    return cleaned


def _parse_date(raw) -> datetime:
    """Attempt multiple date formats."""
    if isinstance(raw, datetime):
        return raw
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(raw).strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"Unparseable date: {raw}")


# ── Public API ───────────────────────────────────────────────────


async def validate_csv(contents: bytes) -> Tuple[pd.DataFrame, List[str]]:
    """
    Parse raw CSV bytes, validate schema and clean data.
    Returns (cleaned_dataframe, list_of_warnings).
    """
    warnings: List[str] = []

    try:
        df = pd.read_csv(StringIO(contents.decode("utf-8-sig")))
    except Exception as exc:
        raise ValueError(f"Cannot parse CSV: {exc}")

    # Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Drop fully empty rows
    df.dropna(how="all", inplace=True)

    # Validate mandatory fields row-by-row
    drop_indices = []
    for idx, row in df.iterrows():
        for col in REQUIRED_COLUMNS:
            if pd.isna(row.get(col)) or str(row[col]).strip() == "":
                warnings.append(f"Row {idx}: missing required field '{col}' — skipped.")
                drop_indices.append(idx)
                break

    df.drop(index=drop_indices, inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Normalise phones
    phone_drops = []
    for idx, row in df.iterrows():
        try:
            df.at[idx, "phone_number"] = _normalise_phone(row["phone_number"])
        except ValueError:
            warnings.append(f"Row {idx} (lead_id={row['lead_id']}): invalid phone — skipped.")
            phone_drops.append(idx)

    df.drop(index=phone_drops, inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Parse dates
    date_drops = []
    for idx, row in df.iterrows():
        try:
            df.at[idx, "last_interaction_date"] = _parse_date(row["last_interaction_date"])
        except ValueError:
            warnings.append(f"Row {idx} (lead_id={row['lead_id']}): invalid date — skipped.")
            date_drops.append(idx)

    df.drop(index=date_drops, inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Fill optional NAs
    for col in OPTIONAL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].fillna("")

    await logger.ainfo(
        "csv_validated",
        total_rows=len(df),
        warnings_count=len(warnings),
    )
    return df, warnings


async def ingest_leads(
    df: pd.DataFrame,
    db: AsyncSession,
    filename: str | None = None,
) -> Batch:
    """
    Persist validated leads to the database under a new batch.
    Duplicate lead_ids within the same batch are updated, not duplicated.
    """
    batch_id = str(uuid.uuid4())[:12]
    batch = Batch(
        batch_id=batch_id,
        filename=filename,
        total_leads=len(df),
        processed_leads=0,
        status="processing",
    )
    db.add(batch)
    await db.flush()

    for _, row in df.iterrows():
        # Upsert logic: check if lead_id already exists
        existing = await db.execute(
            select(Lead).where(Lead.lead_id == str(row["lead_id"]))
        )
        lead = existing.scalar_one_or_none()

        if lead:
            # Reset for re-processing
            lead.full_name = str(row["full_name"]).strip()
            lead.phone_number = str(row["phone_number"]).strip()
            lead.email = str(row.get("email", "")).strip() or None
            lead.last_interaction_date = row["last_interaction_date"]
            lead.lead_source = str(row["lead_source"]).strip()
            lead.notes = str(row.get("notes", "")).strip() or None
            lead.state = LeadState.pending
            lead.batch_id = batch_id
            lead.intent_category = None
            lead.intent_rationale = None
            lead.recommended_angle = None
            lead.sms_tone = None
        else:
            lead = Lead(
                lead_id=str(row["lead_id"]).strip(),
                full_name=str(row["full_name"]).strip(),
                phone_number=str(row["phone_number"]).strip(),
                email=str(row.get("email", "")).strip() or None,
                last_interaction_date=row["last_interaction_date"],
                lead_source=str(row["lead_source"]).strip(),
                notes=str(row.get("notes", "")).strip() or None,
                state=LeadState.pending,
                batch_id=batch_id,
            )
            db.add(lead)

    await db.flush()

    batch.processed_leads = len(df)
    batch.status = "ingested"

    await logger.ainfo("leads_ingested", batch_id=batch_id, count=len(df))
    return batch
