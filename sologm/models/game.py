"""Game model for SoloGM."""

from sqlalchemy import Boolean, Column, String, Text
from sqlalchemy.orm import validates

from sologm.models.base import Base, TimestampMixin
from sologm.models.utils import generate_unique_id, slugify


class Game(Base, TimestampMixin):
    """SQLAlchemy model representing a game in the system."""

    __tablename__ = "games"
    id: Column = Column(String, primary_key=True)
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

    @classmethod
    def create(cls, name: str, description: str) -> "Game":
        """Create a new game with a unique ID based on the name.

        Args:
            name: Name of the game.
            description: Description of the game.
        Returns:
            A new Game instance.
        """
        # Generate a URL-friendly ID from the name
        prefix = slugify(name)
        return cls(
            id=generate_unique_id(prefix),
            name=name,
            description=description
        )
