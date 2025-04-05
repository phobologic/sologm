"""Tests for datetime utilities."""

from datetime import datetime, timedelta, timezone

import pytest
from freezegun import freeze_time

from sologm.utils.datetime_utils import (
    ensure_utc,
    format_datetime,
    get_current_time,
    parse_datetime,
)


@freeze_time("2024-01-01 12:00:00+00:00")
def test_get_current_time():
    """Test getting current time in UTC."""
    current = get_current_time()
    assert current.tzinfo == timezone.utc
    assert current.isoformat() == "2024-01-01T12:00:00+00:00"


def test_parse_datetime():
    """Test parsing datetime strings."""
    # Test parsing UTC datetime
    dt = parse_datetime("2024-01-01T12:00:00+00:00")
    assert dt.tzinfo == timezone.utc
    assert dt.isoformat() == "2024-01-01T12:00:00+00:00"

    # Test parsing naive datetime (should assume UTC)
    dt = parse_datetime("2024-01-01T12:00:00")
    assert dt.tzinfo == timezone.utc
    assert dt.isoformat() == "2024-01-01T12:00:00+00:00"

    # Test parsing other timezone (should convert to UTC)
    dt = parse_datetime("2024-01-01T12:00:00+01:00")
    assert dt.tzinfo == timezone.utc
    assert dt.isoformat() == "2024-01-01T11:00:00+00:00"  # Note the hour difference

    # Test invalid format
    with pytest.raises(ValueError):
        parse_datetime("invalid-datetime")


def test_format_datetime():
    """Test formatting datetime to string."""
    dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    formatted = format_datetime(dt)
    assert formatted == "2024-01-01T12:00:00+00:00"


def test_ensure_utc():
    """Test ensuring datetime is in UTC."""
    # Test with None
    assert ensure_utc(None) is None

    # Test with naive datetime
    naive_dt = datetime(2024, 1, 1, 12, 0)
    utc_dt = ensure_utc(naive_dt)
    assert utc_dt.tzinfo == timezone.utc
    assert utc_dt.isoformat() == "2024-01-01T12:00:00+00:00"

    # Test with UTC datetime
    utc_dt = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    result = ensure_utc(utc_dt)
    assert result.tzinfo == timezone.utc
    assert result.isoformat() == "2024-01-01T12:00:00+00:00"

    # Test with non-UTC timezone
    other_tz = datetime(2024, 1, 1, 12, 0, tzinfo=timezone(offset=timedelta(hours=1)))
    result = ensure_utc(other_tz)
    assert result.tzinfo == timezone.utc
    assert result.isoformat() == "2024-01-01T11:00:00+00:00"  # Note the hour difference
