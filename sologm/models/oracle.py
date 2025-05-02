"""Oracle interpretation models for SoloGM."""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Text, func, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sologm.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from sologm.models.act import Act
    from sologm.models.event import Event
    from sologm.models.game import Game
    from sologm.models.scene import Scene


class InterpretationSet(Base, TimestampMixin):
    """SQLAlchemy model representing a set of oracle interpretations."""

    __tablename__ = "interpretation_sets"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id: Mapped[str] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False
    )
    context: Mapped[str] = mapped_column(Text, nullable=False)
    oracle_results: Mapped[str] = mapped_column(Text, nullable=False)
    retry_attempt: Mapped[int] = mapped_column(Integer, default=0)

    # Flag for current interpretation set in a game
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships this model owns
    interpretations: Mapped[List["Interpretation"]] = relationship(
        "Interpretation",
        back_populates="interpretation_set",
        cascade="all, delete-orphan",
    )

    @property
    def act(self) -> "Act":
        """Get the act this interpretation set belongs to through the scene
        relationship."""
        return self.scene.act

    @property
    def act_id(self) -> str:
        """Get the act ID this interpretation set belongs to."""
        return self.scene.act_id

    @property
    def game(self) -> "Game":
        """Get the game this interpretation set belongs to through the scene
        and act relationships."""
        return self.scene.act.game

    @property
    def game_id(self) -> str:
        """Get the game ID this interpretation set belongs to."""
        return self.scene.act.game_id

    @property
    def selected_interpretation(self) -> Optional["Interpretation"]:
        """Get the selected interpretation from this set, if any.

        This property filters the already loaded interpretations collection
        and doesn't trigger a new database query.
        """
        for interpretation in self.interpretations:
            if interpretation.is_selected:
                return interpretation
        return None

    @hybrid_property
    def has_selection(self) -> bool:
        """Check if this interpretation set has a selected interpretation.

        Works in both Python and SQL contexts:
        - Python: Checks if any interpretation is selected
        - SQL: Performs a subquery to check for selected interpretations
        """
        return any(interp.is_selected for interp in self.interpretations)

    @has_selection.expression
    def has_selection(cls):  # noqa: N805
        """SQL expression for has_selection."""
        from sologm.models.oracle import Interpretation

        return (
            select(1)
            .where((Interpretation.set_id == cls.id) & Interpretation.is_selected)
            .exists()
            .label("has_selection")
        )

    @hybrid_property
    def interpretation_count(self) -> int:
        """Get the number of interpretations in this set.

        Works in both Python and SQL contexts:
        - Python: Returns the length of the interpretations list
        - SQL: Performs a count query
        """
        return len(self.interpretations)

    @interpretation_count.expression
    def interpretation_count(cls):  # noqa: N805
        """SQL expression for interpretation_count."""
        from sologm.models.oracle import Interpretation

        return (
            select(func.count(Interpretation.id))
            .where(Interpretation.set_id == cls.id)
            .label("interpretation_count")
        )

    @classmethod
    def create(
        cls,
        scene_id: str,
        context: str,
        oracle_results: str,
        retry_attempt: int = 0,
        is_current: bool = False,
    ) -> "InterpretationSet":
        """Create a new interpretation set.

        Args:
            scene_id: ID of the scene this interpretation set belongs to.
            context: Context for the interpretation.
            oracle_results: Raw oracle results.
            retry_attempt: Number of retry attempts.
            is_current: Whether this is the current interpretation set.
        Returns:
            A new InterpretationSet instance.
        """
        return cls(
            id=str(uuid.uuid4()),
            scene_id=scene_id,
            context=context,
            oracle_results=oracle_results,
            retry_attempt=retry_attempt,
            is_current=is_current,
        )


class Interpretation(Base, TimestampMixin):
    """SQLAlchemy model representing a single oracle interpretation."""

    __tablename__ = "interpretations"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    set_id: Mapped[str] = mapped_column(
        ForeignKey("interpretation_sets.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(nullable=False)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships this model owns
    events: Mapped[List["Event"]] = relationship(
        "Event", back_populates="interpretation"
    )

    # Removed the recursive property

    @property
    def scene(self) -> "Scene":
        """Get the scene this interpretation belongs to through the interpretation set
        relationship."""
        return self.interpretation_set.scene

    @property
    def scene_id(self) -> str:
        """Get the scene ID this interpretation belongs to."""
        return self.interpretation_set.scene_id

    @property
    def act(self) -> "Act":
        """Get the act this interpretation belongs to through the scene relationship."""
        return self.scene.act

    @property
    def act_id(self) -> str:
        """Get the act ID this interpretation belongs to."""
        return self.scene.act_id

    @property
    def game(self) -> "Game":
        """Get the game this interpretation belongs to through the act relationship."""
        return self.act.game

    @property
    def game_id(self) -> str:
        """Get the game ID this interpretation belongs to."""
        return self.act.game_id

    @property
    def short_description(self) -> str:
        """Get a shortened version of the description.

        This property provides a convenient way to get a preview of the description.
        """
        max_length = 50
        if len(self.description) <= max_length:
            return self.description
        return self.description[:max_length] + "..."

    @hybrid_property
    def event_count(self) -> int:
        """Get the number of events associated with this interpretation.

        Works in both Python and SQL contexts:
        - Python: Returns the length of the events list
        - SQL: Performs a count query
        """
        return len(self.events)

    @event_count.expression
    def event_count(cls):  # noqa: N805
        """SQL expression for event_count."""
        from sologm.models.event import Event

        return (
            select(func.count(Event.id))
            .where(Event.interpretation_id == cls.id)
            .label("event_count")
        )

    @hybrid_property
    def has_events(self) -> bool:
        """Check if this interpretation has any associated events.

        Works in both Python and SQL contexts:
        - Python: Checks if the events list is non-empty
        - SQL: Performs a subquery to check for events
        """
        return len(self.events) > 0

    @has_events.expression
    def has_events(cls):  # noqa: N805
        """SQL expression for has_events."""
        from sologm.models.event import Event

        return (
            select(1)
            .where(Event.interpretation_id == cls.id)
            .exists()
            .label("has_events")
        )

    @property
    def latest_event(self) -> Optional["Event"]:
        """Get the most recently created event for this interpretation, if any.

        This property sorts the already loaded events collection
        and doesn't trigger a new database query.
        """
        if not self.events:
            return None
        return sorted(self.events, key=lambda event: event.created_at, reverse=True)[0]

    @classmethod
    def create(
        cls, set_id: str, title: str, description: str, is_selected: bool = False
    ) -> "Interpretation":
        """Create a new interpretation.

        Args:
            set_id: ID of the interpretation set this interpretation belongs to.
            title: Title of the interpretation.
            description: Description of the interpretation.
            is_selected: Whether this interpretation is selected.
        Returns:
            A new Interpretation instance.
        """
        from sologm.models.utils import slugify

        return cls(
            id=str(uuid.uuid4()),
            set_id=set_id,
            title=title,
            description=description,
            slug=slugify(title),
            is_selected=is_selected,
        )
