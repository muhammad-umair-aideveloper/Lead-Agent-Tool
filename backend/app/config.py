"""
Lead Reactivation Agent — Application Settings
Centralised configuration loaded from environment / .env file.
"""

from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────
    app_name: str = "lead-reactivation-agent"
    app_env: str = "development"
    app_port: int = 8000
    app_secret_key: str = "change-me"

    # ── Database ─────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./data/leads.db"

    # ── Gemini ───────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-pro"

    # ── Twilio ───────────────────────────────────────────────────
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # ── Business hours ───────────────────────────────────────────
    business_hours_start: str = "09:00"
    business_hours_end: str = "17:00"
    business_hours_timezone: str = "America/New_York"

    # ── SMS ──────────────────────────────────────────────────────
    default_sms_tone: str = "professional"
    ignore_timeout_hours: int = 48
    max_retries: int = 3

    # ── CORS ─────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
