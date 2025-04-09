"""Event source model for SoloGM."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from sologm.models.base import Base


class EventSource(Base):
    """SQLAlchemy model representing an event source type."""

    __tablename__ = "event_sources"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Relationships will be defined in relationships.py

    @classmethod
    def create(cls, id: str, name: str) -> "EventSource":
        """Create a new event source type.
        
        Args:
            id: Identifier for the event source
            name: Display name for the event source
            
        Returns:
            A new EventSource instance
        """
        return cls(
            id=id,
            name=name
        )
