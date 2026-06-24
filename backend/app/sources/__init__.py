"""Base adapter interface for data sources."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RawEvent:
    """Normalised intermediate event representation produced by an adapter."""
    title: str
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    raw_excerpt: Optional[str] = None
    event_type: str = "notice"
    company_name: Optional[str] = None
    company_location: Optional[str] = None
    company_registry_id: Optional[str] = None


@dataclass
class FetchResult:
    source_name: str
    events: list[RawEvent] = field(default_factory=list)
    status: str = "ok"      # ok | error | skipped
    error_message: Optional[str] = None
    fetched_at: datetime = field(default_factory=datetime.utcnow)


class BaseAdapter(ABC):
    """All source adapters must implement this interface."""

    name: str = ""
    base_url: str = ""
    mode: str = "active"     # active | degraded
    legal_note: str = ""

    @abstractmethod
    async def fetch(self) -> FetchResult:
        """Fetch new events from the source."""
