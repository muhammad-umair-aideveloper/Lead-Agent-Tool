"""
AI Reasoning Module — Gemini Integration
──────────────────────────────────────────
Leverages Google Gemini 3 Pro for intent classification and message generation.
"""

from __future__ import annotations

import json
from typing import Optional

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.logging_config import logger
from app.models.lead import IntentCategory, SmsTone

# ── Gemini client singleton ─────────────────────────────────────

_model = None


def _get_model():
    global _model
    if _model is None:
        genai.configure(api_key=settings.gemini_api_key)
        _model = genai.GenerativeModel(settings.gemini_model)
    return _model


# ── Prompt engineering ───────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert lead reactivation analyst for a sales team.
Your task is to analyze dormant / cold leads and determine their reactivation potential.

For each lead you receive, you MUST return a JSON object with exactly these keys:
{
  "intent_category": "High Intent" | "Medium Intent" | "Low Intent" | "Not Interested",
  "intent_rationale": "<2-3 sentences explaining your reasoning>",
  "recommended_sms": "<a concise, personalized SMS message (≤160 chars) designed to re-engage this lead>",
  "sms_tone": "professional" | "casual" | "urgency"
}

Rules:
- Analyze ALL provided context: name, last interaction date, lead source, and notes.
- The SMS MUST be unique and personalized — NEVER use a generic template.
- Dynamically select the best tone based on the lead's profile and context.
- If the tone_preference is provided, weight it but you may override if contextually warranted.
- Keep the SMS under 160 characters for single-segment delivery.
- Return ONLY valid JSON, no markdown fences, no extra text.
"""


def _build_lead_prompt(
    full_name: str,
    phone_number: str,
    last_interaction_date: str,
    lead_source: str,
    notes: Optional[str],
    tone_preference: str = "professional",
) -> str:
    return f"""Analyze this dormant lead and generate a reactivation plan:

Lead Name: {full_name}
Phone: {phone_number}
Last Interaction: {last_interaction_date}
Lead Source: {lead_source}
Historical Notes: {notes or "No notes available."}
Preferred Tone: {tone_preference}

Return your analysis as the specified JSON object."""


# ── AI reasoning call ────────────────────────────────────────────


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
async def analyze_lead(
    full_name: str,
    phone_number: str,
    last_interaction_date: str,
    lead_source: str,
    notes: Optional[str] = None,
    tone_preference: str = "professional",
) -> dict:
    """
    Send lead context to Gemini and return structured classification.
    Returns dict with: intent_category, intent_rationale, recommended_sms, sms_tone
    """
    model = _get_model()

    prompt = _build_lead_prompt(
        full_name=full_name,
        phone_number=phone_number,
        last_interaction_date=last_interaction_date,
        lead_source=lead_source,
        notes=notes,
        tone_preference=tone_preference,
    )

    await logger.ainfo("gemini_request", lead_name=full_name)

    import asyncio
    response = await asyncio.to_thread(
        model.generate_content,
        [
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "model", "parts": ["Understood. I will analyze leads and return structured JSON as specified."]},
            {"role": "user", "parts": [prompt]},
        ],
        generation_config=genai.types.GenerationConfig(
            temperature=0.4,
            max_output_tokens=512,
        ),
    )

    raw_text = response.text.strip()

    # Strip markdown fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[-1]
    if raw_text.endswith("```"):
        raw_text = raw_text.rsplit("```", 1)[0]
    raw_text = raw_text.strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        await logger.aerror("gemini_parse_error", raw=raw_text[:500])
        raise ValueError(f"Gemini returned invalid JSON: {raw_text[:200]}")

    # Validate required fields
    required_keys = {"intent_category", "intent_rationale", "recommended_sms", "sms_tone"}
    missing = required_keys - set(result.keys())
    if missing:
        raise ValueError(f"Gemini response missing keys: {missing}")

    # Validate intent_category
    valid_intents = {e.value for e in IntentCategory}
    if result["intent_category"] not in valid_intents:
        raise ValueError(f"Invalid intent_category: {result['intent_category']}")

    # Validate sms_tone
    valid_tones = {e.value for e in SmsTone}
    if result["sms_tone"] not in valid_tones:
        result["sms_tone"] = tone_preference  # Fallback to preference

    await logger.ainfo(
        "gemini_response",
        lead_name=full_name,
        intent=result["intent_category"],
        tone=result["sms_tone"],
    )

    return result
