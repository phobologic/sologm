"""Act model for SoloGM."""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint, func, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from sologm.models.base import Base, TimestampMixin
from sologm.models.utils import slugify

if TYPE_CHECKING:
    from sologm.models.dice import DiceRoll
    from sologm.models.event import Event
    from sologm.models.oracle import Interpretation
    from sologm.models.scene import Scene


class Act(Base, TimestampMixin):
    """SQLAlchemy model representing an act in a game."""

    __tablename__ = "acts"
    __table_args__ = (UniqueConstraint("game_id", "slug", name="uix_game_act_slug"),)

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Mapped[str] = mapped_column(nullable=False, index=True)
    game_id: Mapped[str] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(
        nullable=True
    )  # Can be null for untitled acts
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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

    @hybrid_property
    def has_scenes(self) -> bool:
        """Check if the act has any scenes.

        Works in both Python and SQL contexts:
        - Python: Checks if the scenes list is non-empty
        - SQL: Performs a subquery to check for scenes
        """
        return len(self.scenes) > 0

    @has_scenes.expression
    def has_scenes(cls):  # noqa: N805
        """SQL expression for has_scenes."""
        from sologm.models.scene import Scene

        return select(1).where(Scene.act_id == cls.id).exists().label("has_scenes")

    @hybrid_property
    def scene_count(self) -> int:
        """Get the number of scenes in this act.

        Works in both Python and SQL contexts:
        - Python: Returns the length of the scenes list
        - SQL: Performs a count query
        """
        return len(self.scenes)

    @scene_count.expression
    def scene_count(cls):  # noqa: N805
        """SQL expression for scene_count."""
        from sologm.models.scene import Scene

        return (
            select(func.count(Scene.id))
            .where(Scene.act_id == cls.id)
            .label("scene_count")
        )

    @hybrid_property
    def has_active_scene(self) -> bool:
        """Check if the act has an active scene.

        Works in both Python and SQL contexts:
        - Python: Checks if active_scene is not None
        - SQL: Performs a subquery to check for active scenes
        """
        return any(scene.is_active for scene in self.scenes)

    @has_active_scene.expression
    def has_active_scene(cls):  # noqa: N805
        """SQL expression for has_active_scene."""
        from sologm.models.scene import Scene

        return (
            select(1)
            .where((Scene.act_id == cls.id) & Scene.is_active)
            .exists()
            .label("has_active_scene")
        )

    # has_completed_scenes hybrid property removed (status field removed from Scene)

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

    # completed_scenes property removed (status field removed from Scene)
    # active_scenes property removed (use active_scene or filter scenes by is_active)

    @property
    def latest_scene(self) -> Optional["Scene"]:
        """Get the most recently created scene for this act, if any.

        This property sorts the already loaded scenes collection
        and doesn't trigger a new database query.
        """
        if not self.scenes:
            return None
        return sorted(self.scenes, key=lambda scene: scene.created_at, reverse=True)[0]

    @hybrid_property
    def has_events(self) -> bool:
        """Check if the act has any events across all scenes.

        Works in both Python and SQL contexts:
        - Python: Checks if all_events is non-empty
        - SQL: Performs a subquery to check for events
        """
        return any(len(scene.events) > 0 for scene in self.scenes)

    @has_events.expression
    def has_events(cls):  # noqa: N805
        """SQL expression for has_events."""
        from sologm.models.event import Event
        from sologm.models.scene import Scene

        return (
            select(1)
            .where((Scene.act_id == cls.id) & (Event.scene_id == Scene.id))
            .exists()
            .label("has_events")
        )

    @hybrid_property
    def event_count(self) -> int:
        """Get the total number of events across all scenes.

        Works in both Python and SQL contexts:
        - Python: Returns the length of all_events
        - SQL: Performs a count query
        """
        return sum(len(scene.events) for scene in self.scenes)

    @event_count.expression
    def event_count(cls):  # noqa: N805
        """SQL expression for event_count."""
        from sologm.models.event import Event
        from sologm.models.scene import Scene

        return (
            select(func.count(Event.id))
            .where((Scene.act_id == cls.id) & (Event.scene_id == Scene.id))
            .label("event_count")
        )

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

    @hybrid_property
    def has_dice_rolls(self) -> bool:
        """Check if the act has any dice rolls across all scenes.

        Works in both Python and SQL contexts:
        - Python: Checks if all_dice_rolls is non-empty
        - SQL: Performs a subquery to check for dice rolls
        """
        return any(len(scene.dice_rolls) > 0 for scene in self.scenes)

    @has_dice_rolls.expression
    def has_dice_rolls(cls):  # noqa: N805
        """SQL expression for has_dice_rolls."""
        from sologm.models.dice import DiceRoll
        from sologm.models.scene import Scene

        return (
            select(1)
            .where((Scene.act_id == cls.id) & (DiceRoll.scene_id == Scene.id))
            .exists()
            .label("has_dice_rolls")
        )

    @hybrid_property
    def dice_roll_count(self) -> int:
        """Get the total number of dice rolls across all scenes.

        Works in both Python and SQL contexts:
        - Python: Returns the length of all_dice_rolls
        - SQL: Performs a count query
        """
        return sum(len(scene.dice_rolls) for scene in self.scenes)

    @dice_roll_count.expression
    def dice_roll_count(cls):  # noqa: N805
        """SQL expression for dice_roll_count."""
        from sologm.models.dice import DiceRoll
        from sologm.models.scene import Scene

        return (
            select(func.count(DiceRoll.id))
            .where((Scene.act_id == cls.id) & (DiceRoll.scene_id == Scene.id))
            .label("dice_roll_count")
        )

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

    @hybrid_property
    def has_interpretations(self) -> bool:
        """Check if the act has any interpretations across all scenes.

        Works in both Python and SQL contexts:
        - Python: Checks if all_interpretations is non-empty
        - SQL: Performs a subquery to check for interpretations
        """
        return any(
            any(
                len(interp_set.interpretations) > 0
                for interp_set in scene.interpretation_sets
            )
            for scene in self.scenes
        )

    @has_interpretations.expression
    def has_interpretations(cls):  # noqa: N805
        """SQL expression for has_interpretations."""
        from sologm.models.oracle import Interpretation, InterpretationSet
        from sologm.models.scene import Scene

        return (
            select(1)
            .where(
                (Scene.act_id == cls.id)
                & (InterpretationSet.scene_id == Scene.id)
                & (Interpretation.set_id == InterpretationSet.id)
            )
            .exists()
            .label("has_interpretations")
        )

    @hybrid_property
    def interpretation_count(self) -> int:
        """Get the total number of interpretations across all scenes.

        Works in both Python and SQL contexts:
        - Python: Returns the length of all_interpretations
        - SQL: Performs a count query
        """
        return sum(
            sum(
                len(interp_set.interpretations)
                for interp_set in scene.interpretation_sets
            )
            for scene in self.scenes
        )

    @interpretation_count.expression
    def interpretation_count(cls):  # noqa: N805
        """SQL expression for interpretation_count."""
        from sologm.models.oracle import Interpretation, InterpretationSet
        from sologm.models.scene import Scene

        return (
            select(func.count(Interpretation.id))
            .where(
                (Scene.act_id == cls.id)
                & (InterpretationSet.scene_id == Scene.id)
                & (Interpretation.set_id == InterpretationSet.id)
            )
            .label("interpretation_count")
        )

    @property
    def all_events(self) -> List["Event"]:
        """Get all events across all scenes in this act.

        This property collects events from all scenes without triggering
        new database queries.
        """
        events = []
        for scene in self.scenes:
            events.extend(scene.events)

        return events

    @property
    def all_dice_rolls(self) -> List["DiceRoll"]:
        """Get all dice rolls across all scenes in this act.

        This property collects dice rolls from all scenes without triggering
        new database queries.
        """
        rolls = []
        for scene in self.scenes:
            rolls.extend(scene.dice_rolls)

        return rolls

    @property
    def all_interpretations(self) -> List["Interpretation"]:
        """Get all interpretations across all scenes in this act.

        This property collects interpretations from all scenes without triggering
        new database queries.
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
        summary: Optional[str],
        sequence: int,
    ) -> "Act":
        """Create a new act with a unique ID and slug.

        Args:
            game_id: ID of the game this act belongs to.
            title: Optional title of the act (can be None for untitled acts).
            summary: Optional summary of the act.
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
            summary=summary,
            sequence=sequence,
        )
