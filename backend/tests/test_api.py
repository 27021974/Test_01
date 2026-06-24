"""Integration tests for the REST API."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import init_db, engine, Base
from app.models import Event, Source
from datetime import datetime, timezone


@pytest_asyncio.fixture(autouse=True)
async def setup_db(tmp_path, monkeypatch):
    """Use an in-memory SQLite DB for tests."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    # Re-import settings/engine after monkeypatching
    import app.config as cfg_module
    import importlib

    # Patch the database URL in the engine
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False})

    import app.database as db_module
    monkeypatch.setattr(db_module, "engine", test_engine)

    test_session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(db_module, "AsyncSessionLocal", test_session_factory)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    async with client as c:
        resp = await c.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_list_sources_empty(client):
    async with client as c:
        resp = await c.get("/api/sources")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_events_empty(client):
    async with client as c:
        resp = await c.get("/api/events")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_get_event_not_found(client):
    async with client as c:
        resp = await c.get("/api/events/999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_stats(client):
    async with client as c:
        resp = await c.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "new_events_24h" in data
    assert "new_events_7d" in data
    assert "insolvency_events_24h" in data
    assert "sources" in data


@pytest.mark.asyncio
async def test_fetch_trigger_requires_token(client):
    async with client as c:
        resp = await c.post("/api/jobs/fetch")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_events_insolvency_filter(client):
    """Test that insolvency filter query param is accepted."""
    async with client as c:
        resp = await c.get("/api/events?insolvency=true")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_events_kmu_filter(client):
    """Test that max_employees and max_revenue filter query params are accepted."""
    async with client as c:
        resp = await c.get("/api/events?max_employees=50&max_revenue=10000000")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_events_search_filter(client):
    async with client as c:
        resp = await c.get("/api/events?q=insolvenz")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_events_prioritize_insolvency_score(client):
    import app.database as db_module

    async with db_module.AsyncSessionLocal() as session:
        async with session.begin():
            source = Source(
                name="Test Source",
                base_url="https://example.com",
                enabled=True,
                mode="active",
            )
            session.add(source)
            await session.flush()

            session.add_all(
                [
                    Event(
                        source_id=source.id,
                        title="Nicht priorisiert",
                        insolvency_score=0.1,
                        fetched_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                        event_type="notice",
                        hash="a" * 64,
                    ),
                    Event(
                        source_id=source.id,
                        title="Insolvenz priorisiert",
                        insolvency_score=0.95,
                        fetched_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
                        event_type="insolvency",
                        hash="b" * 64,
                    ),
                ]
            )

    async with client as c:
        resp = await c.get("/api/events")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload[0]["title"] == "Insolvenz priorisiert"
