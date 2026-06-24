"""Unit tests for hash-based event deduplication."""
from datetime import datetime, date

import pytest

from app.hashing import compute_event_hash


def test_same_inputs_produce_same_hash() -> None:
    h1 = compute_event_hash("Insolvenz Muster GmbH", "https://example.com/1", datetime(2024, 1, 15))
    h2 = compute_event_hash("Insolvenz Muster GmbH", "https://example.com/1", datetime(2024, 1, 15))
    assert h1 == h2


def test_different_title_produces_different_hash() -> None:
    h1 = compute_event_hash("Insolvenz Muster GmbH", "https://example.com/1", datetime(2024, 1, 15))
    h2 = compute_event_hash("Insolvenz Muster AG", "https://example.com/1", datetime(2024, 1, 15))
    assert h1 != h2


def test_different_url_produces_different_hash() -> None:
    h1 = compute_event_hash("Insolvenz", "https://example.com/1", None)
    h2 = compute_event_hash("Insolvenz", "https://example.com/2", None)
    assert h1 != h2


def test_title_normalisation() -> None:
    """Extra spaces and case should not affect the hash."""
    h1 = compute_event_hash("  Insolvenz   Muster GmbH  ", None, None)
    h2 = compute_event_hash("insolvenz muster gmbh", None, None)
    assert h1 == h2


def test_date_only_published_at() -> None:
    h1 = compute_event_hash("Test", None, date(2024, 6, 1))
    h2 = compute_event_hash("Test", None, datetime(2024, 6, 1, 12, 0))
    assert h1 == h2, "date and datetime with same date should hash identically"


def test_none_url_and_none_date() -> None:
    h = compute_event_hash("Test event", None, None)
    assert isinstance(h, str)
    assert len(h) == 64  # SHA-256 hex digest


def test_hash_is_64_chars() -> None:
    h = compute_event_hash("any title", "https://x.com", datetime(2024, 1, 1))
    assert len(h) == 64
