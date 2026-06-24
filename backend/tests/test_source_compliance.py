"""Tests for source compliance and source config syncing."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.jobs.fetch_all import _ensure_source
from app.sources.unternehmensregister import UnternehmensregisterAdapter


class _AdapterStub:
    def __init__(self, *, name: str, base_url: str, enabled: bool, mode: str, legal_note: str):
        self.name = name
        self.base_url = base_url
        self.enabled = enabled
        self.mode = mode
        self.legal_note = legal_note


@pytest.mark.asyncio
async def test_ensure_source_updates_all_config_flags():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False})
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        async with session.begin():
            first = _AdapterStub(
                name="Quelle A",
                base_url="https://a.example",
                enabled=True,
                mode="active",
                legal_note="note-1",
            )
            await _ensure_source(session, first)

            second = _AdapterStub(
                name="Quelle A",
                base_url="https://b.example",
                enabled=False,
                mode="degraded",
                legal_note="note-2",
            )
            source = await _ensure_source(session, second)

    assert source.base_url == "https://b.example"
    assert source.enabled is False
    assert source.mode == "degraded"
    assert source.legal_note == "note-2"
    await engine.dispose()


@pytest.mark.asyncio
async def test_unternehmensregister_fetch_skips_when_robots_disallow(monkeypatch):
    monkeypatch.setattr("app.sources.unternehmensregister._robots_allows", lambda _: False)
    adapter = UnternehmensregisterAdapter()
    adapter.enabled = True
    adapter.mode = "rss"

    result = await adapter.fetch()

    assert result.status == "skipped"
    assert result.events == []
    assert "robots.txt" in (result.error_message or "")
