"""Fetch-all job: runs all enabled source adapters and persists events."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.classifier import compute_insolvency_score
from app.database import AsyncSessionLocal, init_db
from app.enrichment import (
    extract_case_number,
    extract_court,
    extract_postal_city,
    infer_bundesland,
    infer_company_name,
    infer_industry,
    infer_legal_form,
    infer_procedure_type,
)
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
            legal_form=raw.company_legal_form,
            location=raw.company_location,
            city=raw.company_city,
            postal_code=raw.company_postal_code,
            bundesland=raw.company_bundesland,
            industry=raw.company_industry,
            industry_code=raw.company_industry_code,
        )
        session.add(company)
        await session.flush()
    else:
        _fill_missing_company_fields(company, raw)
    return company


def _fill_missing_company_fields(company: Company, raw: RawEvent) -> None:
    """Backfill optional enrichment fields without overwriting known data."""
    for field_name in (
        "registry_id",
        "legal_form",
        "location",
        "city",
        "postal_code",
        "bundesland",
        "industry",
        "industry_code",
    ):
        raw_value = getattr(raw, f"company_{field_name}", None)
        if raw_value and getattr(company, field_name) is None:
            setattr(company, field_name, raw_value)


def _enrich_raw_event(raw: RawEvent) -> RawEvent:
    """Populate market-research fields inferred from notice text."""
    text = f"{raw.title} {raw.raw_excerpt or ''}"
    court = raw.court or extract_court(text)
    postal_code, city = extract_postal_city(text)
    industry, industry_code = infer_industry(text)

    raw.company_name = raw.company_name or infer_company_name(text)
    raw.company_legal_form = raw.company_legal_form or infer_legal_form(text)
    raw.company_city = raw.company_city or city
    raw.company_postal_code = raw.company_postal_code or postal_code
    raw.company_bundesland = raw.company_bundesland or infer_bundesland(raw.company_city, court)
    raw.company_industry = raw.company_industry or industry
    raw.company_industry_code = raw.company_industry_code or industry_code
    raw.court = court
    raw.case_number = raw.case_number or extract_case_number(text)
    raw.procedure_type = raw.procedure_type or infer_procedure_type(text)
    return raw


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
        raw = _enrich_raw_event(raw)
        h = compute_event_hash(raw.title, raw.url, raw.published_at)
        score = compute_insolvency_score(f"{raw.title} {raw.raw_excerpt or ''}")

        company = await _get_or_create_company(session, raw)

        event = Event(
            source_id=source.id,
            company_id=company.id if company else None,
            title=raw.title,
            url=raw.url,
            published_at=raw.published_at,
            fetched_at=datetime.now(timezone.utc),
            event_type=raw.event_type,
            insolvency_score=score,
            raw_excerpt=raw.raw_excerpt,
            court=raw.court,
            case_number=raw.case_number,
            procedure_type=raw.procedure_type,
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
