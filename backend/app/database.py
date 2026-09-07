"""SQLAlchemy async database engine and session factory."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Ensure the data directory exists (SQLite)
if settings.database_url.startswith("sqlite"):
    db_path = settings.database_url.replace("sqlite+aiosqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables and apply lightweight SQLite column migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if settings.database_url.startswith("sqlite"):
            await _ensure_sqlite_columns(conn)


async def _ensure_sqlite_columns(conn) -> None:
    """Add optional MVP columns when an existing SQLite DB predates them."""
    migrations = {
        "companies": {
            "legal_form": "VARCHAR(64)",
            "city": "VARCHAR(120)",
            "postal_code": "VARCHAR(12)",
            "bundesland": "VARCHAR(64)",
            "industry": "VARCHAR(120)",
            "industry_code": "VARCHAR(32)",
        },
        "events": {
            "court": "VARCHAR(160)",
            "case_number": "VARCHAR(80)",
            "procedure_type": "VARCHAR(80)",
        },
    }

    for table, columns in migrations.items():
        existing = await conn.execute(text(f"PRAGMA table_info({table})"))
        existing_names = {row[1] for row in existing.fetchall()}
        for column_name, column_type in columns.items():
            if column_name not in existing_names:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_type}"))
