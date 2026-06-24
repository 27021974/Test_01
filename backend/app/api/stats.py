"""GET /api/stats – aggregated statistics."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Event, Source
from app.schemas import SourceOut, StatsOut

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsOut)
async def get_stats(db: AsyncSession = Depends(get_db)) -> StatsOut:
    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)

    async def _count(since: datetime, insolvency_only: bool = False) -> int:
        stmt = select(func.count(Event.id)).where(Event.fetched_at >= since)
        if insolvency_only:
            stmt = stmt.where(Event.insolvency_score >= 0.5)
        result = await db.execute(stmt)
        return result.scalar_one()

    new_24h = await _count(since_24h)
    new_7d = await _count(since_7d)
    ins_24h = await _count(since_24h, insolvency_only=True)
    ins_7d = await _count(since_7d, insolvency_only=True)

    sources_result = await db.execute(select(Source).order_by(Source.name))
    sources = [SourceOut.model_validate(s) for s in sources_result.scalars().all()]

    return StatsOut(
        new_events_24h=new_24h,
        new_events_7d=new_7d,
        insolvency_events_24h=ins_24h,
        insolvency_events_7d=ins_7d,
        sources=sources,
    )
