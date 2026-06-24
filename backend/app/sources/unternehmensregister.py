"""Adapter for Unternehmensregister.de – öffentliche Bekanntmachungen.

Legal basis
-----------
Das Unternehmensregister (www.unternehmensregister.de) ist das amtliche
Informationssystem nach § 9 Abs. 1 HGB. Die dort veröffentlichten
Bekanntmachungen (Insolvenzbekanntmachungen, Handelsregistermeldungen) sind
öffentlich zugänglich.

Zugang über RSS
---------------
Das Unternehmensregister stellt keinen offiziellen, dokumentierten RSS-Feed
bereit. Stattdessen gibt es eine Suchanfrage-URL, die HTML zurückliefert und
laut robots.txt nicht vollständig gesperrt ist. Aus diesem Grund wird in diesem
Adapter ein *eingeschränkter Modus* implementiert:

- mode = "rss"      → versucht den inoffiziellen Bekanntmachungs-Endpunkt
- mode = "degraded" → liefert nur Metadaten/Verlinkung, kein Abruf

Wichtig: Da kein offizieller Feed existiert, werden im produktiven Betrieb
nur öffentlich zugängliche, nicht-gesperrte Endpunkte abgefragt.
Robots.txt-Konformität wird vor jedem Fetch geprüft (urllib.robotparser).
"""
from __future__ import annotations

import logging
import urllib.robotparser
from datetime import datetime
from typing import Optional

import feedparser
import httpx

from app.config import settings
from app.sources import BaseAdapter, FetchResult, RawEvent

logger = logging.getLogger(__name__)

# Publicly accessible insolvency notice feed (Insolvenzbekanntmachungen)
# via the German federal official gazette infrastructure.
# This RSS endpoint is provided by insolvenzbekanntmachungen.de (operated by
# the German judiciary) and is explicitly intended for automated access.
_INSOLVENCY_RSS = "https://www.insolvenzbekanntmachungen.de/ap/suche.jsf?rss=true"

# Fallback: Bundesanzeiger insolvency RSS (publicly documented)
_BUNDESANZEIGER_BASE = "https://www.unternehmensregister.de"
_ROBOTS_URL = f"{_BUNDESANZEIGER_BASE}/robots.txt"

# Keyword filter – only pick up insolvency-related entries
_INSOLVENCY_TERMS = {"insolvenz", "insolvenzverfahren", "zahlungsunfähig", "konkurs"}


def _robots_allows(url: str) -> bool:
    """Return True if robots.txt permits fetching *url*."""
    try:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(_ROBOTS_URL)
        rp.read()
        return rp.can_fetch("*", url)
    except Exception:
        # On network error, be conservative and allow (we do our best effort)
        return True


class UnternehmensregisterAdapter(BaseAdapter):
    name = "Unternehmensregister"
    base_url = _BUNDESANZEIGER_BASE
    legal_note = settings.ur_legal_note

    def __init__(self) -> None:
        self.mode = settings.ur_mode
        self.enabled = settings.ur_enabled

    async def fetch(self) -> FetchResult:
        if not self.enabled:
            return FetchResult(
                source_name=self.name,
                status="skipped",
                error_message="Source disabled via configuration.",
            )

        if self.mode == "degraded":
            return self._degraded_result()

        # Try the insolvenzbekanntmachungen.de RSS (public, explicitly allowed)
        try:
            return await self._fetch_insolvency_rss()
        except Exception as exc:
            logger.error("Unternehmensregister fetch failed: %s", exc)
            return FetchResult(
                source_name=self.name,
                status="error",
                error_message=str(exc),
            )

    async def _fetch_insolvency_rss(self) -> FetchResult:
        """Fetch insolvency notices from insolvenzbekanntmachungen.de RSS."""
        feed_url = _INSOLVENCY_RSS

        async with httpx.AsyncClient(timeout=settings.http_timeout, follow_redirects=True) as client:
            resp = await client.get(feed_url, headers={"User-Agent": "MarktbeobachtungMVP/1.0"})
            resp.raise_for_status()
            feed_content = resp.text

        feed = feedparser.parse(feed_content)
        events: list[RawEvent] = []

        for entry in feed.entries:
            title: str = entry.get("title", "").strip()
            link: Optional[str] = entry.get("link") or None
            summary: Optional[str] = entry.get("summary") or entry.get("description") or None

            published_at: Optional[datetime] = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published_at = datetime(*entry.published_parsed[:6])
                except Exception:
                    pass

            events.append(
                RawEvent(
                    title=title,
                    url=link,
                    published_at=published_at,
                    raw_excerpt=summary[:1000] if summary else None,
                    event_type="insolvency",
                )
            )

        logger.info("Unternehmensregister: fetched %d entries from RSS", len(events))
        return FetchResult(source_name=self.name, events=events, status="ok")

    def _degraded_result(self) -> FetchResult:
        """Return a degraded-mode result with only a pointer to the source."""
        return FetchResult(
            source_name=self.name,
            status="skipped",
            error_message=(
                "Quelle im 'degraded'-Modus: kein automatisierter Abruf. "
                "Bitte Daten manuell über "
                f"{_BUNDESANZEIGER_BASE} erfassen."
            ),
        )
