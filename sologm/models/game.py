"""Game model for SoloGM."""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from sologm.models.base import Base, TimestampMixin
from sologm.models.utils import slugify

if TYPE_CHECKING:
    from sologm.models.scene import Scene


class Game(Base, TimestampMixin):
    """SQLAlchemy model representing a game in the system."""

    __tablename__ = "games"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=False)

    # Relationships this model owns
    scenes: Mapped[List["Scene"]] = relationship(
        "Scene", back_populates="game", cascade="all, delete-orphan"
    )

    @validates("name")
    def validate_name(self, _: str, name: str) -> str:
        """Validate the game name."""
        if not name or not name.strip():
            raise ValueError("Game name cannot be empty")
        return name

    @validates("slug")
    def validate_slug(self, _: str, slug: str) -> str:
        """Validate the game slug."""
        if not slug or not slug.strip():
            raise ValueError("Slug cannot be empty")
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

        return cls(id=unique_id, slug=base_slug, name=name, description=description)
