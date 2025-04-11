"""Scene model for SoloGM."""

import enum
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum, ForeignKey, Integer, Text, UniqueConstraint, func, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from sologm.models.base import Base, TimestampMixin
from sologm.models.utils import slugify

if TYPE_CHECKING:
    from sologm.models.act import Act
    from sologm.models.dice import DiceRoll
    from sologm.models.event import Event
    from sologm.models.game import Game
    from sologm.models.oracle import Interpretation, InterpretationSet


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

    @property
    def latest_event(self) -> Optional["Event"]:
        """Get the most recently created event for this scene, if any.

        This property sorts the already loaded events collection
        and doesn't trigger a new database query.
        """
        if not self.events:
            return None
        return sorted(self.events, key=lambda event: event.created_at, reverse=True)[0]

    @property
    def latest_dice_roll(self) -> Optional["DiceRoll"]:
        """Get the most recently created dice roll for this scene, if any.

        This property sorts the already loaded dice_rolls collection
        and doesn't trigger a new database query.
        """
        if not self.dice_rolls:
            return None
        return sorted(self.dice_rolls, key=lambda roll: roll.created_at, reverse=True)[
            0
        ]

    @property
    def latest_interpretation_set(self) -> Optional["InterpretationSet"]:
        """Get the most recently created interpretation set for this scene, if any.

        This property sorts the already loaded interpretation_sets collection
        and doesn't trigger a new database query.
        """
        if not self.interpretation_sets:
            return None
        return sorted(
            self.interpretation_sets, key=lambda iset: iset.created_at, reverse=True
        )[0]

    @property
    def latest_interpretation(self) -> Optional["Interpretation"]:
        """Get the most recently created interpretation for this scene, if any.

        This property navigates through interpretation sets to find the latest interpretation,
        without triggering new database queries.
        """
        latest_interp = None
        latest_time = None

        for interp_set in self.interpretation_sets:
            for interp in interp_set.interpretations:
                if latest_time is None or interp.created_at > latest_time:
                    latest_interp = interp
                    latest_time = interp.created_at

        return latest_interp

    @property
    def current_interpretation_set(self) -> Optional["InterpretationSet"]:
        """Get the current interpretation set for this scene, if any.

        This property filters the already loaded interpretation_sets collection
        and doesn't trigger a new database query.
        """
        for interp_set in self.interpretation_sets:
            if interp_set.is_current:
                return interp_set
        return None

    @property
    def selected_interpretations(self) -> List["Interpretation"]:
        """Get all selected interpretations for this scene.

        This property collects selected interpretations from all interpretation sets
        without triggering new database queries.
        """
        selected = []
        for interp_set in self.interpretation_sets:
            for interp in interp_set.interpretations:
                if interp.is_selected:
                    selected.append(interp)
        return selected

    @property
    def all_interpretations(self) -> List["Interpretation"]:
        """Get all interpretations for this scene.

        This property collects interpretations from all interpretation sets
        without triggering new database queries.
        """
        all_interps = []
        for interp_set in self.interpretation_sets:
            all_interps.extend(interp_set.interpretations)
        return all_interps

    @property
    def is_completed(self) -> bool:
        """Check if this scene is completed.

        This property provides a more readable way to check the scene status.
        """
        return self.status == SceneStatus.COMPLETED

    @property
    def is_active_status(self) -> bool:
        """Check if this scene has an active status.

        This property provides a more readable way to check the scene status.
        Note: This is different from is_active which indicates if this is the current scene.
        """
        return self.status == SceneStatus.ACTIVE

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

    @hybrid_property
    def has_events(self) -> bool:
        """Check if the scene has any events.

        Works in both Python and SQL contexts:
        - Python: Checks if the events list is non-empty
        - SQL: Performs a subquery to check for events
        """
        return len(self.events) > 0

    @has_events.expression
    def has_events(cls):
        """SQL expression for has_events."""
        from sologm.models.event import Event

        return select(1).where(Event.scene_id == cls.id).exists().label("has_events")

    @hybrid_property
    def event_count(self) -> int:
        """Get the number of events in this scene.

        Works in both Python and SQL contexts:
        - Python: Returns the length of the events list
        - SQL: Performs a count query
        """
        return len(self.events)

    @event_count.expression
    def event_count(cls):
        """SQL expression for event_count."""
        from sologm.models.event import Event

        return (
            select(func.count(Event.id))
            .where(Event.scene_id == cls.id)
            .label("event_count")
        )

    @hybrid_property
    def has_dice_rolls(self) -> bool:
        """Check if the scene has any dice rolls.

        Works in both Python and SQL contexts:
        - Python: Checks if the dice_rolls list is non-empty
        - SQL: Performs a subquery to check for dice rolls
        """
        return len(self.dice_rolls) > 0

    @has_dice_rolls.expression
    def has_dice_rolls(cls):
        """SQL expression for has_dice_rolls."""
        from sologm.models.dice import DiceRoll

        return (
            select(1)
            .where(DiceRoll.scene_id == cls.id)
            .exists()
            .label("has_dice_rolls")
        )

    @hybrid_property
    def dice_roll_count(self) -> int:
        """Get the number of dice rolls in this scene.

        Works in both Python and SQL contexts:
        - Python: Returns the length of the dice_rolls list
        - SQL: Performs a count query
        """
        return len(self.dice_rolls)

    @dice_roll_count.expression
    def dice_roll_count(cls):
        """SQL expression for dice_roll_count."""
        from sologm.models.dice import DiceRoll

        return (
            select(func.count(DiceRoll.id))
            .where(DiceRoll.scene_id == cls.id)
            .label("dice_roll_count")
        )

    @hybrid_property
    def has_interpretation_sets(self) -> bool:
        """Check if the scene has any interpretation sets.

        Works in both Python and SQL contexts:
        - Python: Checks if the interpretation_sets list is non-empty
        - SQL: Performs a subquery to check for interpretation sets
        """
        return len(self.interpretation_sets) > 0

    @has_interpretation_sets.expression
    def has_interpretation_sets(cls):
        """SQL expression for has_interpretation_sets."""
        from sologm.models.oracle import InterpretationSet

        return (
            select(1)
            .where(InterpretationSet.scene_id == cls.id)
            .exists()
            .label("has_interpretation_sets")
        )

    @hybrid_property
    def interpretation_set_count(self) -> int:
        """Get the number of interpretation sets in this scene.

        Works in both Python and SQL contexts:
        - Python: Returns the length of the interpretation_sets list
        - SQL: Performs a count query
        """
        return len(self.interpretation_sets)

    @interpretation_set_count.expression
    def interpretation_set_count(cls):
        """SQL expression for interpretation_set_count."""
        from sologm.models.oracle import InterpretationSet

        return (
            select(func.count(InterpretationSet.id))
            .where(InterpretationSet.scene_id == cls.id)
            .label("interpretation_set_count")
        )

    @hybrid_property
    def has_interpretations(self) -> bool:
        """Check if the scene has any interpretations across all sets.

        Works in both Python and SQL contexts:
        - Python: Checks if all_interpretations is non-empty
        - SQL: Performs a subquery to check for interpretations
        """
        return any(
            len(interp_set.interpretations) > 0
            for interp_set in self.interpretation_sets
        )

    @has_interpretations.expression
    def has_interpretations(cls):
        """SQL expression for has_interpretations."""
        from sologm.models.oracle import InterpretationSet, Interpretation

        return (
            select(1)
            .where(
                (InterpretationSet.scene_id == cls.id)
                & (Interpretation.set_id == InterpretationSet.id)
            )
            .exists()
            .label("has_interpretations")
        )

    @hybrid_property
    def interpretation_count(self) -> int:
        """Get the total number of interpretations across all sets.

        Works in both Python and SQL contexts:
        - Python: Returns the length of all_interpretations
        - SQL: Performs a count query
        """
        return sum(
            len(interp_set.interpretations) for interp_set in self.interpretation_sets
        )

    @interpretation_count.expression
    def interpretation_count(cls):
        """SQL expression for interpretation_count."""
        from sologm.models.oracle import InterpretationSet, Interpretation

        return (
            select(func.count(Interpretation.id))
            .where(
                (InterpretationSet.scene_id == cls.id)
                & (Interpretation.set_id == InterpretationSet.id)
            )
            .label("interpretation_count")
        )

    @hybrid_property
    def has_selected_interpretations(self) -> bool:
        """Check if the scene has any selected interpretations.

        Works in both Python and SQL contexts:
        - Python: Checks if selected_interpretations is non-empty
        - SQL: Performs a subquery to check for selected interpretations
        """
        return any(
            any(interp.is_selected for interp in interp_set.interpretations)
            for interp_set in self.interpretation_sets
        )

    @has_selected_interpretations.expression
    def has_selected_interpretations(cls):
        """SQL expression for has_selected_interpretations."""
        from sologm.models.oracle import InterpretationSet, Interpretation

        return (
            select(1)
            .where(
                (InterpretationSet.scene_id == cls.id)
                & (Interpretation.set_id == InterpretationSet.id)
                & (Interpretation.is_selected == True)
            )
            .exists()
            .label("has_selected_interpretations")
        )

    @hybrid_property
    def selected_interpretation_count(self) -> int:
        """Get the number of selected interpretations.

        Works in both Python and SQL contexts:
        - Python: Returns the length of selected_interpretations
        - SQL: Performs a count query
        """
        return len(self.selected_interpretations)

    @selected_interpretation_count.expression
    def selected_interpretation_count(cls):
        """SQL expression for selected_interpretation_count."""
        from sologm.models.oracle import InterpretationSet, Interpretation

        return (
            select(func.count(Interpretation.id))
            .where(
                (InterpretationSet.scene_id == cls.id)
                & (Interpretation.set_id == InterpretationSet.id)
                & (Interpretation.is_selected == True)
            )
            .label("selected_interpretation_count")
        )

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
