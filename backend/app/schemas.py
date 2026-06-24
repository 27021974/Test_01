"""Pydantic schemas for request/response validation."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ── Source ─────────────────────────────────────────────────────────────────────

class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_url: str
    enabled: bool
    mode: str
    legal_note: Optional[str]
    last_fetch_at: Optional[datetime]
    last_fetch_status: Optional[str]


# ── Company ────────────────────────────────────────────────────────────────────

class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    registry_id: Optional[str]
    employees: Optional[int]
    revenue_eur: Optional[float]
    location: Optional[str]


# ── Event ──────────────────────────────────────────────────────────────────────

class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    source_name: Optional[str] = None
    company_id: Optional[int]
    company_name: Optional[str] = None
    title: str
    url: Optional[str]
    published_at: Optional[datetime]
    fetched_at: datetime
    event_type: str
    insolvency_score: float
    raw_excerpt: Optional[str]
    data_incomplete: bool


class EventDetail(EventOut):
    company: Optional[CompanyOut] = None


# ── Stats ──────────────────────────────────────────────────────────────────────

class StatsOut(BaseModel):
    new_events_24h: int
    new_events_7d: int
    insolvency_events_24h: int
    insolvency_events_7d: int
    sources: list[SourceOut]
