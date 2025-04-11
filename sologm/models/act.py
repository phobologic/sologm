"""Act model for SoloGM."""

import enum
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from sologm.models.base import Base, TimestampMixin
from sologm.models.utils import slugify

if TYPE_CHECKING:
    from sologm.models.dice import DiceRoll
    from sologm.models.event import Event
    from sologm.models.oracle import Interpretation
    from sologm.models.scene import Scene, SceneStatus


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
    title: Mapped[Optional[str]] = mapped_column(
        nullable=True
    )  # Can be null for untitled acts
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

    @property
    def active_scene(self) -> Optional["Scene"]:
        """Get the active scene for this act, if any.

        This property filters the already loaded scenes collection
        and doesn't trigger a new database query.
        """
        for scene in self.scenes:
            if scene.is_active:
                return scene
        return None

    @property
    def completed_scenes(self) -> List["Scene"]:
        """Get all completed scenes for this act.

        This property filters the already loaded scenes collection
        and doesn't trigger a new database query.
        """
        from sologm.models.scene import SceneStatus

        return [scene for scene in self.scenes if scene.status == SceneStatus.COMPLETED]

    @property
    def active_scenes(self) -> List["Scene"]:
        """Get all active scenes for this act.

        This property filters the already loaded scenes collection
        and doesn't trigger a new database query.
        """
        from sologm.models.scene import SceneStatus

        return [scene for scene in self.scenes if scene.status == SceneStatus.ACTIVE]

    @property
    def latest_scene(self) -> Optional["Scene"]:
        """Get the most recently created scene for this act, if any.

        This property sorts the already loaded scenes collection
        and doesn't trigger a new database query.
        """
        if not self.scenes:
            return None
        return sorted(self.scenes, key=lambda scene: scene.created_at, reverse=True)[0]

    @property
    def first_scene(self) -> Optional["Scene"]:
        """Get the first scene (by sequence) for this act, if any.

        This property sorts the already loaded scenes collection
        and doesn't trigger a new database query.
        """
        if not self.scenes:
            return None
        return sorted(self.scenes, key=lambda scene: scene.sequence)[0]

    @property
    def latest_event(self) -> Optional["Event"]:
        """Get the most recently created event across all scenes in this act.

        This property navigates through scenes to find the latest event,
        without triggering new database queries.
        """
        latest_event = None
        latest_time = None

        for scene in self.scenes:
            for event in scene.events:
                if latest_time is None or event.created_at > latest_time:
                    latest_event = event
                    latest_time = event.created_at

        return latest_event

    @property
    def latest_dice_roll(self) -> Optional["DiceRoll"]:
        """Get the most recently created dice roll across all scenes in this act.

        This property navigates through scenes to find the latest dice roll,
        without triggering new database queries.
        """
        latest_roll = None
        latest_time = None

        for scene in self.scenes:
            for roll in scene.dice_rolls:
                if latest_time is None or roll.created_at > latest_time:
                    latest_roll = roll
                    latest_time = roll.created_at

        return latest_roll

    @property
    def latest_interpretation(self) -> Optional["Interpretation"]:
        """Get the most recently created interpretation across all scenes in this act.

        This property navigates through scenes and interpretation sets to find
        the latest interpretation, without triggering new database queries.
        """
        latest_interp = None
        latest_time = None

        for scene in self.scenes:
            for interp_set in scene.interpretation_sets:
                for interp in interp_set.interpretations:
                    if latest_time is None or interp.created_at > latest_time:
                        latest_interp = interp
                        latest_time = interp.created_at

        return latest_interp

    @property
    def all_events(self) -> List["Event"]:
        """Get all events across all scenes in this act.

        This property collects events from all scenes without triggering new database queries.
        """
        events = []
        for scene in self.scenes:
            events.extend(scene.events)

        return events

    @property
    def all_dice_rolls(self) -> List["DiceRoll"]:
        """Get all dice rolls across all scenes in this act.

        This property collects dice rolls from all scenes without triggering new database queries.
        """
        rolls = []
        for scene in self.scenes:
            rolls.extend(scene.dice_rolls)

        return rolls

    @property
    def all_interpretations(self) -> List["Interpretation"]:
        """Get all interpretations across all scenes in this act.

        This property collects interpretations from all scenes without triggering new database queries.
        """
        interpretations = []
        for scene in self.scenes:
            for interp_set in scene.interpretation_sets:
                interpretations.extend(interp_set.interpretations)

        return interpretations

    @property
    def selected_interpretations(self) -> List["Interpretation"]:
        """Get all selected interpretations across all scenes in this act.

        This property collects selected interpretations from all scenes
        without triggering new database queries.
        """
        return [interp for interp in self.all_interpretations if interp.is_selected]

    @classmethod
    def create(
        cls,
        game_id: str,
        title: Optional[str],
        description: Optional[str],
        sequence: int,
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
