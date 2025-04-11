"""Scene model for SoloGM."""

import enum
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Enum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from sologm.models.base import Base, TimestampMixin
from sologm.models.utils import slugify

if TYPE_CHECKING:
    from sologm.models.act import Act
    from sologm.models.dice import DiceRoll
    from sologm.models.event import Event
    from sologm.models.game import Game
    from sologm.models.oracle import InterpretationSet


class SceneStatus(enum.Enum):
    """Enumeration of possible scene statuses."""

    ACTIVE = "active"
    COMPLETED = "completed"


class Scene(Base, TimestampMixin):
    """SQLAlchemy model representing a scene in a game."""

    __tablename__ = "scenes"
    __table_args__ = (UniqueConstraint("act_id", "slug", name="uix_act_scene_slug"),)

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Mapped[str] = mapped_column(nullable=False, index=True)
    act_id: Mapped[str] = mapped_column(ForeignKey("acts.id"), nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[SceneStatus] = mapped_column(
        Enum(SceneStatus), nullable=False, default=SceneStatus.ACTIVE
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False)

    # Relationships this model owns
    events: Mapped[List["Event"]] = relationship(
        "Event", back_populates="scene", cascade="all, delete-orphan"
    )
    interpretation_sets: Mapped[List["InterpretationSet"]] = relationship(
        "InterpretationSet", back_populates="scene", cascade="all, delete-orphan"
    )
    dice_rolls: Mapped[List["DiceRoll"]] = relationship(
        "DiceRoll", back_populates="scene"
    )

    @property
    def game(self) -> "Game":
        """Get the game this scene belongs to through the act relationship."""
        return self.act.game

    @property
    def game_id(self) -> str:
        """Get the game ID this scene belongs to."""
        return self.act.game_id

    @validates("title")
    def validate_title(self, _: str, title: str) -> str:
        """Validate the scene title."""
        if not title or not title.strip():
            raise ValueError("Scene title cannot be empty")
        return title

    @validates("slug")
    def validate_slug(self, _: str, slug: str) -> str:
        """Validate the scene slug."""
        if not slug or not slug.strip():
            raise ValueError("Scene slug cannot be empty")
        return slug

    @classmethod
    def create(
        cls, act_id: str, title: str, description: str, sequence: int
    ) -> "Scene":
        """Create a new scene with a unique ID and slug based on the title.

        Args:
            act_id: ID of the act this scene belongs to.
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
            act_id=act_id,
            title=title,
            description=description,
            status=SceneStatus.ACTIVE,
            sequence=sequence,
        )
