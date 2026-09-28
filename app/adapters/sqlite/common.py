from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> str:
    """Return an ISO-8601 UTC timestamp for persistence records."""
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value: str) -> datetime:
    """Parse timestamps stored by this adapter."""
    return datetime.fromisoformat(value)
