"""Configuration via environment variables."""
from __future__ import annotations

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "Marktbeobachtung MVP"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/marktbeobachtung.db"

    # Security – simple static token to protect POST /api/jobs/fetch
    api_token: str = "change-me-in-production"

    # Scheduler – hour of day (UTC) when the daily fetch job runs
    scheduler_hour: int = 3

    # HTTP fetch timeouts (seconds)
    http_timeout: int = 30

    # Unternehmensregister adapter
    ur_enabled: bool = True
    ur_mode: str = "rss"  # "rss" | "degraded"
    ur_legal_note: str = (
        "Daten stammen aus dem öffentlichen Bereich des Unternehmensregisters "
        "(§ 9 HGB). Nur öffentlich zugängliche Bekanntmachungen werden abgerufen."
    )

    # Creditreform adapter
    cr_enabled: bool = True
    cr_mode: str = "degraded"  # Always degraded – no public API
    cr_legal_note: str = (
        "Creditreform erlaubt kein automatisiertes Auslesen (robots.txt). "
        "Diese Quelle ist im 'degraded'-Modus: nur manuelle Erfassung / Verlinkung."
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
