"""Event model for SoloGM."""

import uuid
from typing import Optional

from sqlalchemy import Column, ForeignKey, String, Text

from sologm.models.base import Base, TimestampMixin


class Event(Base, TimestampMixin):
    """SQLAlchemy model representing a game event."""

    __tablename__ = "events"
    id: Column = Column(String(36), primary_key=True,
                        default=lambda: str(uuid.uuid4()))
    scene_id: Column = Column(String, ForeignKey("scenes.id"), nullable=False)
    game_id: Column = Column(String, ForeignKey("games.id"), nullable=False)
    description: Column = Column(Text, nullable=False)
    source: Column = Column(String, nullable=False)  # manual, oracle, dice

    # Optional link to interpretation if this event was created from one
    interpretation_id: Column = Column(String, ForeignKey("interpretations.id"),
                                       nullable=True)

    # Relationships will be defined in __init__.py

    @classmethod
    def create(
        cls,
        game_id: str,
        scene_id: str,
        description: str,
        source: str = "manual",
        interpretation_id: Optional[str] = None
    ) -> "Event":
        """Create a new event.

        Args:
            game_id: ID of the game this event belongs to.
            scene_id: ID of the scene this event belongs to.
            description: Description of the event.
            source: Source of the event (manual, oracle, dice).
            interpretation_id: Optional ID of the interpretation that created
                               this event.
        Returns:
            A new Event instance.
        """
        return cls(
            id=str(uuid.uuid4()),
            game_id=game_id,
            scene_id=scene_id,
            description=description,
            source=source,
            interpretation_id=interpretation_id
        )
