"""Game model for SoloGM."""

import uuid

from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.orm import validates

from sologm.models.base import Base, TimestampMixin
from sologm.models.utils import slugify


class Game(Base, TimestampMixin):
    """SQLAlchemy model representing a game in the system."""

    __tablename__ = "games"
    id: Column = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Column = Column(String, unique=True, nullable=False, index=True)
    name: Column = Column(String, nullable=False)
    description: Column = Column(Text)
    is_active: Column = Column(Boolean, default=False)

    # Relationships will be defined in __init__.py

    @validates('name')
    def validate_name(self, _: str, name: str) -> str:
        """Validate the game name."""
        if not name or not name.strip():
            raise ValueError("Game name cannot be empty")
        return name

    @validates('slug')
    def validate_slug(self, _: str, slug: str) -> str:
        """Validate the game slug."""
        if not slug or not slug.strip():
            raise ValueError("Game slug cannot be empty")
        return slug

    @classmethod
    def create(cls, name: str, description: str) -> "Game":
        """Create a new game with a unique ID and slug based on the name.

        Args:
            name: Name of the game.
            description: Description of the game.
        Returns:
            A new Game instance.
        """
        # Generate a URL-friendly slug from the name
        base_slug = slugify(name)

        # Create a unique ID
        unique_id = str(uuid.uuid4())

        return cls(
            id=unique_id,
            slug=base_slug,
            name=name,
            description=description
        )
