"""
ORM models for leads and messages.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ── Enums ────────────────────────────────────────────────────────


class LeadState(str, enum.Enum):
    """Lead lifecycle states."""
    pending = "pending"
    message_sent = "message_sent"
    replied = "replied"
    ignored = "ignored"
    opted_out = "opted_out"


class IntentCategory(str, enum.Enum):
    """AI-assigned intent categories."""
    high = "High Intent"
    medium = "Medium Intent"
    low = "Low Intent"
    not_interested = "Not Interested"


class SmsTone(str, enum.Enum):
    professional = "professional"
    casual = "casual"
    urgency = "urgency"


# ── Lead ─────────────────────────────────────────────────────────


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(String(64), unique=True, nullable=False, index=True)
    full_name = Column(String(256), nullable=False)
    phone_number = Column(String(32), nullable=False)
    email = Column(String(256), nullable=True)
    last_interaction_date = Column(DateTime, nullable=False)
    lead_source = Column(String(128), nullable=False)
    notes = Column(Text, nullable=True)

    # AI enrichment
    intent_category = Column(Enum(IntentCategory), nullable=True)
    intent_rationale = Column(Text, nullable=True)
    recommended_angle = Column(Text, nullable=True)
    sms_tone = Column(Enum(SmsTone), nullable=True)

    # State machine
    state = Column(Enum(LeadState), default=LeadState.pending, nullable=False, index=True)

    # Batch tracking
    batch_id = Column(String(64), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    messages = relationship("Message", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lead {self.lead_id} state={self.state}>"


# ── Message ──────────────────────────────────────────────────────


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(String(64), ForeignKey("leads.lead_id"), nullable=False, index=True)

    # Content
    direction = Column(String(8), nullable=False)  # "outbound" | "inbound"
    body = Column(Text, nullable=False)

    # Twilio metadata
    twilio_sid = Column(String(64), nullable=True)
    twilio_status = Column(String(32), nullable=True)

    # Audit metadata
    intent_score = Column(String(32), nullable=True)
    message_variant = Column(String(64), nullable=True)
    sms_tone = Column(Enum(SmsTone), nullable=True)

    # Timestamps
    sent_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    lead = relationship("Lead", back_populates="messages")

    def __repr__(self):
        return f"<Message {self.id} dir={self.direction} lead={self.lead_id}>"


# ── Batch ────────────────────────────────────────────────────────


class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(64), unique=True, nullable=False, index=True)
    filename = Column(String(512), nullable=True)
    total_leads = Column(Integer, default=0)
    processed_leads = Column(Integer, default=0)
    status = Column(String(32), default="processing")  # processing | completed | failed
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Batch {self.batch_id} status={self.status}>"
