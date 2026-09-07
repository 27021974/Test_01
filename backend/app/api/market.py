"""GET /api/market-insights – insolvency market aggregates."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Iterable

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Event
from app.schemas import BucketOut, EventOut, MarketInsightsOut, TrendPointOut

router = APIRouter(prefix="/api/market-insights", tags=["market-insights"])


@router.get("", response_model=MarketInsightsOut)
async def get_market_insights(
    days: int = Query(180, ge=1, le=1825),
    db: AsyncSession = Depends(get_db),
) -> MarketInsightsOut:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.company), selectinload(Event.source))
        .where(Event.insolvency_score >= 0.5)
        .where(Event.fetched_at >= since)
        .order_by(Event.fetched_at.desc())
        .limit(5000)
    )
    events = list(result.scalars().all())

    latest_events: list[EventOut] = []
    for event in events[:10]:
        item = EventOut.model_validate(event)
        item.source_name = event.source.name if event.source else None
        item.company_name = event.company.name if event.company else None
        latest_events.append(item)

    return MarketInsightsOut(
        total_insolvency_events=len(events),
        data_incomplete_events=sum(1 for event in events if event.data_incomplete),
        by_bundesland=_top_buckets(event.company.bundesland if event.company else None for event in events),
        by_industry=_top_buckets(event.company.industry if event.company else None for event in events),
        by_procedure_type=_top_buckets(event.procedure_type for event in events),
        by_court=_top_buckets(event.court for event in events),
        monthly_trend=_monthly_trend(events),
        latest_events=latest_events,
    )


def _top_buckets(values: Iterable[str | None], limit: int = 8) -> list[BucketOut]:
    counter = Counter(value or "Unbekannt" for value in values)
    return [BucketOut(label=label, count=count) for label, count in counter.most_common(limit)]


def _monthly_trend(events: list[Event]) -> list[TrendPointOut]:
    counter: Counter[str] = Counter()
    for event in events:
        timestamp = event.published_at or event.fetched_at
        counter[timestamp.strftime("%Y-%m")] += 1
    return [TrendPointOut(period=period, count=counter[period]) for period in sorted(counter)]
