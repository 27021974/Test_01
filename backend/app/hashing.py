"""Hash helpers for event deduplication."""
from __future__ import annotations

import hashlib
from datetime import date, datetime
from typing import Optional


def compute_event_hash(title: str, url: Optional[str], published_at: Optional[datetime | date]) -> str:
    """Compute a stable SHA-256 hex digest for deduplication.

    Normalises title (lower-case, stripped whitespace) and combines it with
    the URL (if present) and the date portion of *published_at* (if present).
    """
    title_norm = " ".join(title.lower().split())
    url_norm = (url or "").strip().rstrip("/")

    if isinstance(published_at, datetime):
        date_norm = published_at.date().isoformat()
    elif isinstance(published_at, date):
        date_norm = published_at.isoformat()
    else:
        date_norm = ""

    raw = f"{title_norm}|{url_norm}|{date_norm}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
