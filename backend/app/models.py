"""SQLAlchemy ORM models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    base_url: Mapped[str] = mapped_column(String(512), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    mode: Mapped[str] = mapped_column(String(32), default="active")  # active | degraded
    legal_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_fetch_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_fetch_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # ok | error | skipped

    events: Mapped[list["Event"]] = relationship("Event", back_populates="source")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    registry_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    legal_form: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    employees: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    revenue_eur: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    bundesland: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    industry: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)
    industry_code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    events: Mapped[list["Event"]] = relationship("Event", back_populates="company")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False)
    company_id: Mapped[Optional[int]] = mapped_column(ForeignKey("companies.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), default="notice")  # notice | insolvency | other
    insolvency_score: Mapped[float] = mapped_column(Float, default=0.0)
    raw_excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    court: Mapped[Optional[str]] = mapped_column(String(160), nullable=True, index=True)
    case_number: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    procedure_type: Mapped[Optional[str]] = mapped_column(String(80), nullable=True, index=True)
    hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    # Completeness flag: True when employees/revenue data is missing
    data_incomplete: Mapped[bool] = mapped_column(Boolean, default=False)

    source: Mapped["Source"] = relationship("Source", back_populates="events")
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="events")

    __table_args__ = (UniqueConstraint("hash", name="uq_event_hash"),)
