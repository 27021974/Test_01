"""GET /api/events – list and filter events."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Company, Event, Source
from app.schemas import EventDetail, EventOut

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[EventOut])
async def list_events(
    insolvency: Optional[bool] = Query(None, description="Filter für Insolvenz-Events (score >= 0.5)"),
    max_employees: Optional[int] = Query(None, description="Maximale Mitarbeiterzahl"),
    max_revenue: Optional[float] = Query(None, description="Maximaler Jahresumsatz in EUR"),
    source: Optional[str] = Query(None, description="Quellen-Name (teilweise Übereinstimmung)"),
    bundesland: Optional[str] = Query(None, description="Bundesland"),
    industry: Optional[str] = Query(None, description="Branche (teilweise Übereinstimmung)"),
    procedure_type: Optional[str] = Query(None, description="Verfahrensart"),
    q: Optional[str] = Query(None, description="Volltextsuche in Titel, Auszug und Unternehmensname"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[EventOut]:
    stmt = (
        select(Event)
        .options(selectinload(Event.source), selectinload(Event.company))
        .order_by(Event.fetched_at.desc())
    )

    if insolvency is True:
        stmt = stmt.where(Event.insolvency_score >= 0.5)
    elif insolvency is False:
        stmt = stmt.where(Event.insolvency_score < 0.5)

    # Join Company once (outer) if any company-based filter is requested.
    # Outer join preserves events without an associated company (data_incomplete).
    needs_company_join = any(
        value is not None
        for value in (max_employees, max_revenue, bundesland, industry)
    )
    company_joined = False
    if needs_company_join:
        stmt = stmt.join(Event.company, isouter=True)
        company_joined = True
        if max_employees is not None:
            stmt = stmt.where(
                (Event.company_id.is_(None))
                | (Company.employees.is_(None))
                | (Company.employees <= max_employees)
            )
        if max_revenue is not None:
            stmt = stmt.where(
                (Event.company_id.is_(None))
                | (Company.revenue_eur.is_(None))
                | (Company.revenue_eur < max_revenue)
            )
        if bundesland:
            stmt = stmt.where(Company.bundesland == bundesland)
        if industry:
            stmt = stmt.where(Company.industry.ilike(f"%{industry}%"))

    if source:
        stmt = stmt.join(Event.source).where(Source.name.ilike(f"%{source}%"))

    if procedure_type:
        stmt = stmt.where(Event.procedure_type == procedure_type)

    if q:
        if not company_joined:
            stmt = stmt.join(Event.company, isouter=True)
        stmt = stmt.where(
            or_(
                Event.title.ilike(f"%{q}%"),
                Event.raw_excerpt.ilike(f"%{q}%"),
                Company.name.ilike(f"%{q}%"),
            )
        )

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    out = []
    for ev in rows:
        item = EventOut.model_validate(ev)
        item.source_name = ev.source.name if ev.source else None
        item.company_name = ev.company.name if ev.company else None
        out.append(item)
    return out


@router.get("/{event_id}", response_model=EventDetail)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)) -> EventDetail:
    result = await db.execute(
        select(Event)
        .options(selectinload(Event.source), selectinload(Event.company))
        .where(Event.id == event_id)
    )
    ev = result.scalar_one_or_none()
    if ev is None:
        raise HTTPException(status_code=404, detail="Event not found")

    item = EventDetail.model_validate(ev)
    item.source_name = ev.source.name if ev.source else None
    item.company_name = ev.company.name if ev.company else None
    return item
