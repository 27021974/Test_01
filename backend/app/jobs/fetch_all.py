"""Fetch-all job: runs all enabled source adapters and persists events."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.classifier import compute_insolvency_score
from app.database import AsyncSessionLocal, init_db
from app.hashing import compute_event_hash
from app.models import Company, Event, Source
from app.sources import FetchResult, RawEvent
from app.sources.creditreform import CreditreformAdapter
from app.sources.unternehmensregister import UnternehmensregisterAdapter

logger = logging.getLogger(__name__)

ADAPTERS = [
    UnternehmensregisterAdapter(),
    CreditreformAdapter(),
]


async def _ensure_source(session, adapter) -> Source:
    """Upsert source row and return the ORM object."""
    result = await session.execute(select(Source).where(Source.name == adapter.name))
    source = result.scalar_one_or_none()
    if source is None:
        source = Source(
            name=adapter.name,
            base_url=adapter.base_url,
            enabled=adapter.enabled,
            mode=adapter.mode,
            legal_note=adapter.legal_note,
        )
        session.add(source)
        await session.flush()
    else:
        source.mode = adapter.mode
        source.legal_note = adapter.legal_note
    return source


async def _get_or_create_company(session, raw: RawEvent) -> Company | None:
    """Return existing or create new Company row for a raw event."""
    if not raw.company_name:
        return None

    result = await session.execute(
        select(Company).where(Company.name == raw.company_name)
    )
    company = result.scalar_one_or_none()
    if company is None:
        company = Company(
            name=raw.company_name,
            registry_id=raw.company_registry_id,
            location=raw.company_location,
        )
        session.add(company)
        await session.flush()
    return company


async def _persist_result(session, source: Source, result: FetchResult) -> int:
    """Persist events from a FetchResult into the DB. Returns count of new events."""
    # Update source status
    source.last_fetch_at = result.fetched_at
    source.last_fetch_status = result.status
    await session.flush()

    if result.status != "ok":
        logger.info("Source %s: status=%s, skipping event persist", result.source_name, result.status)
        return 0

    new_count = 0
    for raw in result.events:
        h = compute_event_hash(raw.title, raw.url, raw.published_at)
        score = compute_insolvency_score(f"{raw.title} {raw.raw_excerpt or ''}")

        company = await _get_or_create_company(session, raw)

        event = Event(
            source_id=source.id,
            company_id=company.id if company else None,
            title=raw.title,
            url=raw.url,
            published_at=raw.published_at,
            fetched_at=datetime.utcnow(),
            event_type=raw.event_type,
            insolvency_score=score,
            raw_excerpt=raw.raw_excerpt,
            hash=h,
            data_incomplete=(company is None or company.employees is None or company.revenue_eur is None),
        )
        session.add(event)
        try:
            # Use a nested savepoint so a duplicate-hash violation only rolls
            # back this single event, not the entire batch.
            async with session.begin_nested():
                await session.flush()
            new_count += 1
        except IntegrityError:
            # Duplicate – skip silently (savepoint already rolled back)
            logger.debug("Duplicate event skipped (hash=%s)", h)

    return new_count


async def run_fetch_all() -> dict:
    """Main entry point – runs all adapters and returns a summary."""
    await init_db()

    summary: dict = {}
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for adapter in ADAPTERS:
                logger.info("Fetching source: %s (mode=%s)", adapter.name, adapter.mode)
                result = await adapter.fetch()
                source = await _ensure_source(session, adapter)
                count = await _persist_result(session, source, result)
                summary[adapter.name] = {
                    "status": result.status,
                    "new_events": count,
                    "error": result.error_message,
                }
                logger.info("Source %s: %d new events, status=%s", adapter.name, count, result.status)

    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = asyncio.run(run_fetch_all())
    print(result)
