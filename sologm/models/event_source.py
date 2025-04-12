"""Event source model for SoloGM."""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from sologm.models.base import Base


class EventSource(Base):
    """SQLAlchemy model representing an event source type."""

    __tablename__ = "event_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    # Relationships will be defined in relationships.py

    @classmethod
    def create(cls, name: str) -> "EventSource":
        """Create a new event source type.

        Args:
            name: Name of the event source (e.g., 'manual', 'oracle', 'dice')

        Returns:
            A new EventSource instance
        """
        return cls(name=name)
