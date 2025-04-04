"""Base SQLAlchemy models and utilities for SoloGM."""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime
from datetime import datetime
from sologm.utils.datetime_utils import get_current_time

Base = declarative_base()

class TimestampMixin:
    """Mixin that adds created_at and modified_at columns."""
    created_at = Column(DateTime, default=get_current_time, nullable=False)
    modified_at = Column(DateTime, default=get_current_time, onupdate=get_current_time, nullable=False)
