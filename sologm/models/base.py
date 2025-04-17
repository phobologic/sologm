"""Base SQLAlchemy models and utilities for SoloGM."""

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, mapped_column

from sologm.utils.datetime_utils import get_current_time


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class TimestampMixin:
    """Mixin that adds created_at and modified_at columns."""

    created_at = mapped_column(DateTime, default=get_current_time, nullable=False)
    modified_at = mapped_column(
        DateTime, default=get_current_time, onupdate=get_current_time, nullable=False
    )
