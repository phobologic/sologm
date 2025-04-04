"""Scene model for SoloGM."""

import enum
import uuid
from typing import ClassVar

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
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
    __table_args__ = (
        UniqueConstraint('game_id', 'slug', name='uix_game_scene_slug'),
    )
    
    id: Column = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Column = Column(String, nullable=False, index=True)
    game_id: Column = Column(String, ForeignKey("games.id"), nullable=False)
    title: Column = Column(String, nullable=False)
    description: Column = Column(Text)
    status: Column = Column(Enum(SceneStatus), nullable=False,
                            default=SceneStatus.ACTIVE)
    sequence: Column = Column(Integer, nullable=False)
    is_active: Column = Column(Boolean, default=False)

    # Relationships will be defined in __init__.py

    @validates('title')
    def validate_title(self, _: str, title: str) -> str:
        """Validate the scene title."""
        if not title or not title.strip():
            raise ValueError("Scene title cannot be empty")
        return title
        
    @validates('slug')
    def validate_slug(self, _: str, slug: str) -> str:
        """Validate the scene slug."""
        if not slug or not slug.strip():
            raise ValueError("Scene slug cannot be empty")
        return slug

    @classmethod
    def create(
        cls,
        game_id: str,
        title: str,
        description: str,
        sequence: int
    ) -> "Scene":
        """Create a new scene with a unique ID and slug based on the title.

        Args:
            game_id: ID of the game this scene belongs to.
            title: Title of the scene.
            description: Description of the scene.
            sequence: Sequence number of the scene.
        Returns:
            A new Scene instance.
        """
        # Generate a URL-friendly slug from the title and sequence
        scene_slug = f"scene-{sequence}-{slugify(title)}"
        
        return cls(
            id=str(uuid.uuid4()),
            slug=scene_slug,
            game_id=game_id,
            title=title,
            description=description,
            status=SceneStatus.ACTIVE,
            sequence=sequence
        )
