"""Event model for SoloGM."""

import uuid
from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sologm.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from sologm.models.event_source import EventSource
    from sologm.models.game import Game


class Event(Base, TimestampMixin):
    """SQLAlchemy model representing a game event."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id: Mapped[str] = mapped_column(ForeignKey("scenes.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("event_sources.id"), nullable=False
    )

    # Optional link to interpretation if this event was created from one
    interpretation_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("interpretations.id"), nullable=True
    )

    # Define the "owning" relationship here
    source: Mapped["EventSource"] = relationship("EventSource")

    # Relationships will be defined in relationships.py

    @property
    def game(self) -> "Game":
        """Get the game this event belongs to through the scene relationship."""
        return self.scene.act.game

    @property
    def game_id(self) -> str:
        """Get the game ID this event belongs to (for backward compatibility)."""
        return self.scene.act.game_id

    @classmethod
    def create(
        cls,
        scene_id: str,
        description: str,
        source_id: int,
        interpretation_id: Optional[str] = None,
    ) -> "Event":
        """Create a new event.

        Args:
            scene_id: ID of the scene this event belongs to.
            description: Description of the event.
            source_id: ID of the event source.
            interpretation_id: Optional ID of the interpretation that created
                               this event.
        Returns:
            A new Event instance.
        """
        return cls(
            id=str(uuid.uuid4()),
            scene_id=scene_id,
            description=description,
            source_id=source_id,
            interpretation_id=interpretation_id,
        )
