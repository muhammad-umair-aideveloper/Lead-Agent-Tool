"""
Twilio webhook handlers.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.twilio_sms import parse_inbound_sms
from app.services.state_machine import handle_inbound_reply
from app.logging_config import logger

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


@router.post("/twilio/inbound")
async def twilio_inbound(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Twilio inbound SMS webhook handler.
    Processes incoming text messages and updates lead states.
    """
    form_data = await request.form()
    form_dict = dict(form_data)

    await logger.ainfo("twilio_webhook_received", data=form_dict)

    parsed = await parse_inbound_sms(form_dict)

    result = await handle_inbound_reply(
        db=db,
        from_number=parsed["from_number"],
        body=parsed["body"],
        twilio_sid=parsed["twilio_sid"],
    )
    await db.commit()

    # Return TwiML empty response
    twiml = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    return Response(content=twiml, media_type="application/xml")


@router.post("/twilio/status")
async def twilio_status_callback(request: Request):
    """
    Twilio message status callback.
    Updates message delivery status.
    """
    form_data = await request.form()
    form_dict = dict(form_data)

    await logger.ainfo("twilio_status_callback", data=form_dict)

    # In a production system you'd update the Message.twilio_status here
    return {"status": "received"}
