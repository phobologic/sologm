"""Scene model for SoloGM."""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from sologm.models.base import Base, TimestampMixin
from sologm.models.utils import slugify

if TYPE_CHECKING:
    from sologm.models.act import (
        Act,
    )  # Added Act for relationship back_populates type hint
    from sologm.models.dice import DiceRoll
    from sologm.models.event import Event
    from sologm.models.game import Game
    from sologm.models.oracle import Interpretation, InterpretationSet


class Scene(Base, TimestampMixin):
    """SQLAlchemy model representing a scene in a game."""

    __tablename__ = "scenes"
    __table_args__ = (UniqueConstraint("act_id", "slug", name="uix_act_scene_slug"),)

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    slug: Mapped[str] = mapped_column(nullable=False, index=True)
    act_id: Mapped[str] = mapped_column(
        ForeignKey("acts.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    # Status column was removed; is_active flag now indicates the current scene.
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        default=False, index=True
    )  # True if this is the current scene being played in its act.

    # Relationships
    events: Mapped[List["Event"]] = relationship(
        "Event",
        back_populates="scene",
        cascade="all, delete-orphan",
        lazy="selectin",  # Consider selectin loading for performance
    )
    interpretation_sets: Mapped[List["InterpretationSet"]] = relationship(
        "InterpretationSet",
        back_populates="scene",
        cascade="all, delete-orphan",
        lazy="selectin",  # Consider selectin loading for performance
    )
    dice_rolls: Mapped[List["DiceRoll"]] = relationship(
        "DiceRoll",
        back_populates="scene",
        cascade="all, delete-orphan",  # Added cascade to match ondelete
        lazy="selectin",  # Use selectin loading for potential performance gain.
    )

    # Define the relationship back to Act within TYPE_CHECKING to avoid circular imports.
    if TYPE_CHECKING:
        act: Mapped["Act"]

    # --- Accessor Properties ---

    @property
    def game(self) -> "Game":
        """Get the Game this scene belongs to via the Act relationship.

        Requires the 'act' relationship (and its 'game' relationship) to be loaded.
        """
        if not hasattr(self, "act") or self.act is None:
            # This typically indicates a programming error if accessed when not loaded.
            raise AttributeError(
                "The 'act' relationship is not loaded on this Scene object."
            )
        return self.act.game

    @property
    def game_id(self) -> str:
        """Get the game ID this scene belongs to via the Act relationship.

        Requires the 'act' relationship to be loaded.
        """
        if not hasattr(self, "act") or self.act is None:
            raise AttributeError(
                "The 'act' relationship is not loaded on this Scene object."
            )
        return self.act.game_id

    # --- Latest Item Properties (using loaded relationships) ---

    @property
    def latest_event(self) -> Optional["Event"]:
        """Get the most recently created event from the loaded 'events' collection.

        Returns:
            The most recent Event object, or None if no events are loaded/present.
        """
        if not self.events:
            return None
        return sorted(self.events, key=lambda event: event.created_at, reverse=True)[0]

    @property
    def latest_dice_roll(self) -> Optional["DiceRoll"]:
        """Get the most recently created roll from the loaded 'dice_rolls' collection.

        Returns:
            The most recent DiceRoll object, or None if no rolls are loaded/present.
        """
        if not self.dice_rolls:
            return None
        return sorted(self.dice_rolls, key=lambda roll: roll.created_at, reverse=True)[
            0
        ]

    @property
    def latest_interpretation_set(self) -> Optional["InterpretationSet"]:
        """Get the most recent set from the loaded 'interpretation_sets' collection.

        Returns:
            The most recent InterpretationSet object, or None if no sets are
            loaded/present.
        """
        if not self.interpretation_sets:
            return None
        return sorted(
            self.interpretation_sets, key=lambda iset: iset.created_at, reverse=True
        )[0]

    @property
    def latest_interpretation(self) -> Optional["Interpretation"]:
        """Get the most recent interpretation across all loaded interpretation sets.

        Navigates through loaded 'interpretation_sets' and their 'interpretations'.

        Returns:
            The most recent Interpretation object, or None if no interpretations
            are loaded/present.
        """
        latest_interp = None
        latest_time = None

        for interp_set in self.interpretation_sets:
            for interp in interp_set.interpretations:
                if latest_time is None or interp.created_at > latest_time:
                    latest_interp = interp
                    latest_time = interp.created_at

        return latest_interp

    # --- Interpretation Set Properties (using loaded relationships) ---

    @property
    def current_interpretation_set(self) -> Optional["InterpretationSet"]:
        """Get the current set from the loaded 'interpretation_sets' collection.

        Filters the loaded collection based on the 'is_current' flag.

        Returns:
            The current InterpretationSet object, or None if none is marked as current.
        """
        for interp_set in self.interpretation_sets:
            if interp_set.is_current:
                return interp_set
        return None

    @property
    def selected_interpretations(self) -> List["Interpretation"]:
        """Get all selected interpretations from loaded interpretation sets.

        Collects interpretations where 'is_selected' is True across loaded sets.

        Returns:
            A list of selected Interpretation objects.
        """
        selected = []
        for interp_set in self.interpretation_sets:
            for interp in interp_set.interpretations:
                if interp.is_selected:
                    selected.append(interp)
        return selected

    @property
    def all_interpretations(self) -> List["Interpretation"]:
        """Get all interpretations from all loaded interpretation sets.

        Returns:
            A list of all Interpretation objects associated with this scene.
        """
        all_interps = []
        for interp_set in self.interpretation_sets:
            all_interps.extend(interp_set.interpretations)
        return all_interps

    # --- Validators ---

    @validates("title")
    def validate_title(self, _: str, title: str) -> str:
        """Ensure the scene title is not empty or just whitespace."""
        if not title or not title.strip():
            raise ValueError("Scene title cannot be empty")
        return title.strip()

    @validates("slug")
    def validate_slug(self, _: str, slug: str) -> str:
        """Ensure the scene slug is not empty or just whitespace."""
        if not slug or not slug.strip():
            raise ValueError("Scene slug cannot be empty")
        return slugify(slug)

    # --- Hybrid Properties (for efficient querying) ---

    @hybrid_property
    def has_events(self) -> bool:
        """Check if the scene has any associated events.

        Works in Python (checks loaded 'events') and SQL (uses EXISTS subquery).
        """
        return bool(self.events)

    @has_events.expression
    def has_events(cls):
        """SQL expression for checking the existence of related events."""
        from sologm.models.event import Event

        return select(Event.id).where(Event.scene_id == cls.id).exists()

    @hybrid_property
    def event_count(self) -> int:
        """Get the number of events associated with this scene.

        Works in Python (returns len of loaded 'events') and SQL (uses COUNT query).
        """
        return len(self.events)

    @event_count.expression
    def event_count(cls):
        """SQL expression for counting related events."""
        from sologm.models.event import Event

        return (
            select(func.count(Event.id))
            .where(Event.scene_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def has_dice_rolls(self) -> bool:
        """Check if the scene has any associated dice rolls.

        Works in Python (checks loaded 'dice_rolls') and SQL (uses EXISTS subquery).
        """
        return bool(self.dice_rolls)

    @has_dice_rolls.expression
    def has_dice_rolls(cls):
        """SQL expression for checking the existence of related dice rolls."""
        from sologm.models.dice import DiceRoll

        return select(DiceRoll.id).where(DiceRoll.scene_id == cls.id).exists()

    @hybrid_property
    def dice_roll_count(self) -> int:
        """Get the number of dice rolls associated with this scene.

        Works in Python (returns len of loaded 'dice_rolls') and SQL (uses COUNT query).
        """
        return len(self.dice_rolls)

    @dice_roll_count.expression
    def dice_roll_count(cls):
        """SQL expression for counting related dice rolls."""
        from sologm.models.dice import DiceRoll

        return (
            select(func.count(DiceRoll.id))
            .where(DiceRoll.scene_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def has_interpretation_sets(self) -> bool:
        """Check if the scene has any associated interpretation sets.

        Works in Python (checks loaded 'interpretation_sets') and SQL (uses EXISTS subquery).
        """
        return bool(self.interpretation_sets)

    @has_interpretation_sets.expression
    def has_interpretation_sets(cls):
        """SQL expression for checking the existence of related interpretation sets."""
        from sologm.models.oracle import InterpretationSet

        return (
            select(InterpretationSet.id)
            .where(InterpretationSet.scene_id == cls.id)
            .exists()
        )

    @hybrid_property
    def interpretation_set_count(self) -> int:
        """Get the number of interpretation sets associated with this scene.

        Works in Python (returns len of loaded 'interpretation_sets') and SQL (uses COUNT query).
        """
        return len(self.interpretation_sets)

    @interpretation_set_count.expression
    def interpretation_set_count(cls):
        """SQL expression for counting related interpretation sets."""
        from sologm.models.oracle import InterpretationSet

        return (
            select(func.count(InterpretationSet.id))
            .where(InterpretationSet.scene_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def has_interpretations(self) -> bool:
        """Check if the scene has any interpretations across all sets.

        Works in Python (checks loaded sets/interpretations) and SQL (uses EXISTS subquery).
        """
        return any(iset.interpretations for iset in self.interpretation_sets)

    @has_interpretations.expression
    def has_interpretations(cls):
        """SQL expression for checking the existence of related interpretations."""
        from sologm.models.oracle import Interpretation, InterpretationSet

        return (
            select(Interpretation.id)
            .join(InterpretationSet, Interpretation.set_id == InterpretationSet.id)
            .where(InterpretationSet.scene_id == cls.id)
            .exists()
        )

    @hybrid_property
    def interpretation_count(self) -> int:
        """Get the total number of interpretations across all sets.

        Works in Python (sums len of loaded 'interpretations') and SQL (uses COUNT query).
        """
        return sum(len(iset.interpretations) for iset in self.interpretation_sets)

    @interpretation_count.expression
    def interpretation_count(cls):
        """SQL expression for counting related interpretations."""
        from sologm.models.oracle import Interpretation, InterpretationSet

        return (
            select(func.count(Interpretation.id))
            .join(InterpretationSet, Interpretation.set_id == InterpretationSet.id)
            .where(InterpretationSet.scene_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def has_selected_interpretations(self) -> bool:
        """Check if the scene has any selected interpretations.

        Works in Python (checks loaded interpretations) and SQL (uses EXISTS subquery).
        """
        return any(
            interp.is_selected
            for iset in self.interpretation_sets
            for interp in iset.interpretations
        )

    @has_selected_interpretations.expression
    def has_selected_interpretations(cls):
        """SQL expression for checking the existence of selected interpretations."""
        from sologm.models.oracle import Interpretation, InterpretationSet

        return (
            select(Interpretation.id)
            .join(InterpretationSet, Interpretation.set_id == InterpretationSet.id)
            .where(InterpretationSet.scene_id == cls.id)
            .where(Interpretation.is_selected)
            .exists()
        )

    @hybrid_property
    def selected_interpretation_count(self) -> int:
        """Get the number of selected interpretations across all sets.

        Works in Python (counts selected in loaded interpretations) and SQL (uses COUNT query).
        """
        count = 0
        for iset in self.interpretation_sets:
            for interp in iset.interpretations:
                if interp.is_selected:
                    count += 1
        return count

    @selected_interpretation_count.expression
    def selected_interpretation_count(cls):
        """SQL expression for counting selected interpretations."""
        from sologm.models.oracle import Interpretation, InterpretationSet

        return (
            select(func.count(Interpretation.id))
            .join(InterpretationSet, Interpretation.set_id == InterpretationSet.id)
            .where(InterpretationSet.scene_id == cls.id)
            .where(Interpretation.is_selected)
            .scalar_subquery()
        )

    # --- Class Methods ---

    @classmethod
    def create(
        cls, act_id: str, title: str, description: Optional[str], sequence: int
    ) -> "Scene":
        """Create a new scene instance with a unique ID and generated slug.

        Note: This method creates the instance but does not add it to the session.

        Args:
            act_id: ID of the act this scene belongs to.
            title: Title of the scene (will be stripped).
            description: Optional description of the scene (will be stripped if provided).
            sequence: Sequence number of the scene within the act.

        Returns:
            A new, transient Scene instance.

        Raises:
            ValueError: If title is empty or whitespace.
        """
        clean_title = title.strip() if title else ""
        if not clean_title:
            raise ValueError("Scene title cannot be empty")

        clean_description = description.strip() if description else None

        scene_slug = f"scene-{sequence}-{slugify(clean_title)}"

        return cls(
            id=str(uuid.uuid4()),
            slug=scene_slug,
            act_id=act_id,
            title=clean_title,
            description=clean_description,
            sequence=sequence,
            # is_active defaults to False via the mapped_column definition.
        )
