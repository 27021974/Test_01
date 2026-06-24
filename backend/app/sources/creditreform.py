"""Adapter for Creditreform – DEGRADED mode only.

Legal / robots.txt status
--------------------------
Creditreform (www.creditreform.de) untersagt in ihrer robots.txt das
automatisierte Auslesen durch Webcrawler und stellt keine öffentliche API
bereit. Ein automatisierter Zugriff würde gegen die Nutzungsbedingungen
verstoßen.

Daher ist dieser Adapter **dauerhaft im 'degraded'-Modus** implementiert:
- Es werden keine HTTP-Anfragen an creditreform.de gestellt.
- Das Frontend zeigt eine klare Kennzeichnung, warum diese Quelle nur
  eingeschränkt verfügbar ist.
- Datenpflege erfolgt manuell über die Admin-API (POST /api/events).

Zukünftige Erweiterung
-----------------------
Sollte Creditreform eine offizielle Datenschnittstelle (API/Feed) anbieten,
kann hier der Adapter durch Setzen von ``mode = "active"`` aktiviert werden.
"""
from __future__ import annotations

import logging

from app.config import settings
from app.sources import BaseAdapter, FetchResult

logger = logging.getLogger(__name__)


class CreditreformAdapter(BaseAdapter):
    name = "Creditreform"
    base_url = "https://www.creditreform.de/forderungsmanagement/inkasso"
    mode = "degraded"  # Cannot be changed – no public API
    legal_note = settings.cr_legal_note

    def __init__(self) -> None:
        self.enabled = settings.cr_enabled

    async def fetch(self) -> FetchResult:
        """Always returns degraded – no automated fetch is possible."""
        if not self.enabled:
            return FetchResult(
                source_name=self.name,
                status="skipped",
                error_message="Source disabled via configuration.",
            )

        logger.info(
            "Creditreform adapter: degraded mode – no automated fetch. "
            "Manual data entry required."
        )
        return FetchResult(
            source_name=self.name,
            status="skipped",
            error_message=(
                "Creditreform erlaubt kein automatisiertes Auslesen (robots.txt). "
                "Bitte Daten manuell über https://www.creditreform.de erfassen."
            ),
        )
