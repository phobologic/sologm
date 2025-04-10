"""Act model for SoloGM."""

import enum
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from sologm.models.base import Base, TimestampMixin
from sologm.models.utils import slugify

if TYPE_CHECKING:
    from sologm.models.scene import Scene


class ActStatus(enum.Enum):
    """Enumeration of possible act statuses."""
    
    ACTIVE = "active"
    COMPLETED = "completed"


class Act(Base, TimestampMixin):
    """SQLAlchemy model representing an act in a game."""
    
    __tablename__ = "acts"
    __table_args__ = (UniqueConstraint("game_id", "slug", name="uix_game_act_slug"),)
    
    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Mapped[str] = mapped_column(nullable=False, index=True)
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(nullable=True)  # Can be null for untitled acts
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ActStatus] = mapped_column(
        Enum(ActStatus), nullable=False, default=ActStatus.ACTIVE
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False)
    
    # Relationships this model owns
    scenes: Mapped[List["Scene"]] = relationship(
        "Scene", back_populates="act", cascade="all, delete-orphan"
    )
    
    @validates("slug")
    def validate_slug(self, _: str, slug: str) -> str:
        """Validate the act slug."""
        if not slug or not slug.strip():
            raise ValueError("Act slug cannot be empty")
        return slug
    
    @classmethod
    def create(
        cls, game_id: str, title: Optional[str], description: Optional[str], sequence: int
    ) -> "Act":
        """Create a new act with a unique ID and slug.
        
        Args:
            game_id: ID of the game this act belongs to.
            title: Optional title of the act (can be None for untitled acts).
            description: Optional description of the act.
            sequence: Sequence number of the act.
        Returns:
            A new Act instance.
        """
        # Generate a URL-friendly slug from the title and sequence
        # For untitled acts, use a placeholder
        if title:
            act_slug = f"act-{sequence}-{slugify(title)}"
        else:
            act_slug = f"act-{sequence}-untitled"
            
        return cls(
            id=str(uuid.uuid4()),
            slug=act_slug,
            game_id=game_id,
            title=title,
            description=description,
            status=ActStatus.ACTIVE,
            sequence=sequence,
        )
