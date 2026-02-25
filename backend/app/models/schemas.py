"""
Pydantic schemas for request / response validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Lead Schemas ─────────────────────────────────────────────────


class LeadCSVRow(BaseModel):
    """Validates a single row from the uploaded CSV."""
    lead_id: str
    full_name: str
    phone_number: str
    email: Optional[str] = None
    last_interaction_date: str
    lead_source: str
    notes: Optional[str] = None


class LeadOut(BaseModel):
    """Public representation of a lead."""
    id: int
    lead_id: str
    full_name: str
    phone_number: str
    email: Optional[str] = None
    last_interaction_date: datetime
    lead_source: str
    notes: Optional[str] = None
    intent_category: Optional[str] = None
    intent_rationale: Optional[str] = None
    recommended_angle: Optional[str] = None
    sms_tone: Optional[str] = None
    state: str
    batch_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeadListOut(BaseModel):
    leads: List[LeadOut]
    total: int
    page: int
    page_size: int


# ── Message Schemas ──────────────────────────────────────────────


class MessageOut(BaseModel):
    id: int
    lead_id: str
    direction: str
    body: str
    twilio_sid: Optional[str] = None
    twilio_status: Optional[str] = None
    intent_score: Optional[str] = None
    message_variant: Optional[str] = None
    sms_tone: Optional[str] = None
    sent_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Batch Schemas ────────────────────────────────────────────────


class BatchOut(BaseModel):
    id: int
    batch_id: str
    filename: Optional[str] = None
    total_leads: int
    processed_leads: int
    status: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Analytics Schemas ────────────────────────────────────────────


class DashboardKPIs(BaseModel):
    total_leads: int = 0
    total_messages_sent: int = 0
    total_replies: int = 0
    total_ignored: int = 0
    total_opted_out: int = 0
    reply_rate: float = 0.0
    ignored_rate: float = 0.0
    avg_reply_time_minutes: Optional[float] = None


class IntentBreakdown(BaseModel):
    intent_category: str
    count: int
    reply_count: int
    reply_rate: float


class DashboardData(BaseModel):
    kpis: DashboardKPIs
    intent_breakdown: List[IntentBreakdown]
    state_distribution: Dict[str, int]
    source_distribution: Dict[str, int]
    daily_messages: List[Dict[str, Any]]


# ── Config Schemas ───────────────────────────────────────────────


class AppConfigOut(BaseModel):
    business_hours_start: str
    business_hours_end: str
    business_hours_timezone: str
    default_sms_tone: str
    ignore_timeout_hours: int
    max_retries: int


class AppConfigUpdate(BaseModel):
    business_hours_start: Optional[str] = None
    business_hours_end: Optional[str] = None
    business_hours_timezone: Optional[str] = None
    default_sms_tone: Optional[str] = None
    ignore_timeout_hours: Optional[int] = None
    max_retries: Optional[int] = None
