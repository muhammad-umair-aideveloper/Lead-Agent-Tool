"""
Twilio SMS Module
──────────────────
Handles outbound messaging, business-hour enforcement, and webhook processing.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

import pytz
from twilio.rest import Client as TwilioClient

from app.config import settings
from app.logging_config import logger

# ── Twilio client singleton ──────────────────────────────────────

_client: TwilioClient | None = None


def _get_client() -> TwilioClient:
    global _client
    if _client is None:
        _client = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)
    return _client


# ── Business hours check ─────────────────────────────────────────


def is_within_business_hours(
    tz_name: str | None = None,
    start: str | None = None,
    end: str | None = None,
) -> bool:
    """Return True if current time is within configured business hours."""
    tz = pytz.timezone(tz_name or settings.business_hours_timezone)
    now = datetime.now(tz)

    start_h, start_m = map(int, (start or settings.business_hours_start).split(":"))
    end_h, end_m = map(int, (end or settings.business_hours_end).split(":"))

    current_minutes = now.hour * 60 + now.minute
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m

    # Also check weekdays (Mon-Fri = 0-4)
    if now.weekday() > 4:
        return False

    return start_minutes <= current_minutes < end_minutes


# ── Send SMS ─────────────────────────────────────────────────────


async def send_sms(
    to_number: str,
    body: str,
    intent_score: str | None = None,
    message_variant: str | None = None,
) -> dict:
    """
    Send an SMS via Twilio.
    Returns dict with twilio_sid, status, sent_at.
    """
    if not is_within_business_hours():
        await logger.awarn("sms_outside_business_hours", to=to_number)
        return {
            "twilio_sid": None,
            "status": "deferred",
            "sent_at": None,
            "reason": "outside_business_hours",
        }

    client = _get_client()

    # Build status callback URL (to be configured per-deployment)
    try:
        message = await asyncio.to_thread(
            client.messages.create,
            body=body,
            from_=settings.twilio_phone_number,
            to=to_number,
        )

        await logger.ainfo(
            "sms_sent",
            twilio_sid=message.sid,
            to=to_number,
            intent_score=intent_score,
        )

        return {
            "twilio_sid": message.sid,
            "status": message.status,
            "sent_at": datetime.utcnow(),
        }

    except Exception as exc:
        await logger.aerror("sms_send_error", to=to_number, error=str(exc))
        raise


# ── Handle inbound webhook ───────────────────────────────────────


async def parse_inbound_sms(form_data: dict) -> dict:
    """
    Parse Twilio inbound SMS webhook payload.
    Returns normalised dict with from_number, body, twilio_sid.
    """
    return {
        "from_number": form_data.get("From", ""),
        "body": form_data.get("Body", ""),
        "twilio_sid": form_data.get("MessageSid", ""),
        "to_number": form_data.get("To", ""),
        "num_media": int(form_data.get("NumMedia", 0)),
    }


# ── Opt-out detection ────────────────────────────────────────────

OPT_OUT_KEYWORDS = {"stop", "unsubscribe", "cancel", "quit", "opt out", "optout", "end"}


def is_opt_out(message_body: str) -> bool:
    """Check if inbound message signals opt-out."""
    return message_body.strip().lower() in OPT_OUT_KEYWORDS
