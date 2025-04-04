"""DateTime utilities for Solo RPG Helper."""

from datetime import datetime, timezone
from typing import Optional


def get_current_time() -> datetime:
    """Get current time in UTC."""
    return datetime.now(timezone.utc)


def parse_datetime(dt_str: str) -> datetime:
    """Parse datetime string and ensure UTC timezone."""
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO format string."""
    return dt.isoformat()


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure a datetime is in UTC timezone."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
