"""Scene model for SoloGM."""

import enum
from typing import Optional, ClassVar

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import validates

from sologm.models.base import Base, TimestampMixin
from sologm.models.utils import slugify


class SceneStatus(enum.Enum):
    """Enumeration of possible scene statuses."""
    ACTIVE = "active"
    COMPLETED = "completed"

class Scene(Base, TimestampMixin):
    """SQLAlchemy model representing a scene in a game."""

    __tablename__: ClassVar[str] = "scenes"
    id: Column = Column(String, primary_key=True)
    game_id: Column = Column(String, ForeignKey("games.id"), nullable=False)
    title: Column = Column(String, nullable=False)
    description: Column = Column(Text)
    status: Column = Column(Enum(SceneStatus), nullable=False, default=SceneStatus.ACTIVE)
    sequence: Column = Column(Integer, nullable=False)
    is_active: Column = Column(Boolean, default=False)

    # Relationships will be defined in __init__.py

    @validates('title')
    def validate_title(self, _: str, title: str) -> str:
        """Validate the scene title."""
        if not title or not title.strip():
            raise ValueError("Scene title cannot be empty")
        return title

    @classmethod
    def create(cls, game_id: str, title: str, description: str, sequence: int) -> "Scene":
        """Create a new scene with a unique ID based on the title.

        Args:
            game_id: ID of the game this scene belongs to.
            title: Title of the scene.
            description: Description of the scene.
            sequence: Sequence number of the scene.
        Returns:
            A new Scene instance.
        """
        # Generate a URL-friendly ID from the title
        prefix = f"scene-{sequence}-{slugify(title)}"
        return cls(
            id=prefix,  # We use the prefix directly as it's already unique enough
            game_id=game_id,
            title=title,
            description=description,
            status=SceneStatus.ACTIVE,
            sequence=sequence
        )
