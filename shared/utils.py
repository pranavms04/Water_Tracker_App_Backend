"""Shared utilities across domain features."""

from datetime import date, datetime, timedelta, timezone
from typing import List


def get_utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


def generate_date_range(start_date: date, end_date: date) -> List[date]:
    """Generate an inclusive list of calendar dates from start_date to end_date."""
    if start_date > end_date:
        return []
    delta = (end_date - start_date).days
    return [start_date + timedelta(days=i) for i in range(delta + 1)]
