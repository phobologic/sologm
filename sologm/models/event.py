"""Event model for SoloGM."""

import uuid
from typing import TYPE_CHECKING, Optional

# Add ondelete="CASCADE" to the ForeignKey import if needed, but it's a string argument
from sqlalchemy import ForeignKey, Text, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sologm.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from sologm.models.act import Act
    from sologm.models.event_source import EventSource
    from sologm.models.game import Game
    from sologm.models.scene import Scene  # Import Scene
    from sologm.models.oracle import Interpretation  # Added for relationship type hint


class Event(Base, TimestampMixin):
    """SQLAlchemy model representing a game event."""

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    # Add ondelete="CASCADE" to the ForeignKey definition
    scene_id: Mapped[str] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("event_sources.id"), nullable=False
    )

    # Optional link to interpretation if this event was created from one
    interpretation_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("interpretations.id"), nullable=True
    )

    # Define the "owning" relationship here
    source: Mapped["EventSource"] = relationship("EventSource")

    # Relationships will be defined in relationships.py
    if TYPE_CHECKING:
        scene: Mapped["Scene"]
        interpretation: Mapped[Optional["Interpretation"]]

    @property
    def game(self) -> "Game":
        """Get the game this event belongs to through the scene relationship."""
        # Add check for scene relationship being loaded
        if not hasattr(self, "scene") or self.scene is None:
            raise AttributeError("Scene relationship not loaded on Event object.")
        return self.scene.act.game

    @hybrid_property
    def game_id(self) -> str:
        """Get the game ID this event belongs to.

        Works in both Python and SQL contexts:
        - Python: Returns the game ID through relationships
        - SQL: Performs a subquery to get the game ID
        """
        # Add check for scene relationship being loaded in Python mode
        if hasattr(self, "scene") and self.scene is not None:
            if hasattr(self.scene, "act") and self.scene.act is not None:
                return self.scene.act.game_id
            else:
                # This path might indicate an issue if accessed when act isn't loaded
                # Consider raising or returning None/default based on expected usage
                raise AttributeError(
                    "Act relationship not loaded on Scene object within Event."
                )
        # If accessed in a way where relationships aren't loaded (e.g., direct query)
        # this part might not be hit directly, relying on the expression below.
        # However, direct attribute access implies loaded state.
        # Let's raise for clarity if relationships aren't ready.
        raise AttributeError("Scene or Act relationship not loaded on Event object.")

    @game_id.expression
    def game_id(cls):  # noqa: N805
        """SQL expression for game_id."""
        from sologm.models.act import Act
        from sologm.models.scene import Scene

        return (
            select(Act.game_id)
            .join(Scene, Scene.act_id == Act.id)
            .where(Scene.id == cls.scene_id)
            .scalar_subquery()
        ).label("game_id")

    @property
    def act(self) -> "Act":
        """Get the act this event belongs to through the scene relationship."""
        # Add check for scene relationship being loaded
        if not hasattr(self, "scene") or self.scene is None:
            raise AttributeError("Scene relationship not loaded on Event object.")
        return self.scene.act

    @hybrid_property
    def act_id(self) -> str:
        """Get the act ID this event belongs to.

        Works in both Python and SQL contexts:
        - Python: Returns the act ID through relationships
        - SQL: Performs a subquery to get the act ID
        """
        # Add check for scene relationship being loaded in Python mode
        if hasattr(self, "scene") and self.scene is not None:
            return self.scene.act_id
        raise AttributeError("Scene relationship not loaded on Event object.")

    @act_id.expression
    def act_id(cls):  # noqa: N805
        """SQL expression for act_id."""
        from sologm.models.scene import Scene

        return (
            select(Scene.act_id).where(Scene.id == cls.scene_id).scalar_subquery()
        ).label("act_id")

    @hybrid_property
    def is_from_oracle(self) -> bool:
        """Check if this event was created from an oracle interpretation.

        Works in both Python and SQL contexts:
        - Python: Checks if interpretation_id is not None
        - SQL: Performs a direct column comparison
        """
        return self.interpretation_id is not None

    @is_from_oracle.expression
    def is_from_oracle(cls):  # noqa: N805
        """SQL expression for is_from_oracle."""
        return (cls.interpretation_id.is_not(None)).label("is_from_oracle")

    @property
    def source_name(self) -> str:
        """Get the name of the event source.

        This property provides a convenient way to access the source name.
        Requires the 'source' relationship to be loaded.
        """
        if not hasattr(self, "source") or self.source is None:
            # This indicates a programming error if accessed when not loaded.
            raise AttributeError(
                "The 'source' relationship is not loaded on this Event object."
            )
        return (
            self.source.name
        )  # Removed unnecessary check now that AttributeError is raised

    @hybrid_property
    def is_manual(self) -> bool:
        """Check if this event was manually created.

        Works in both Python and SQL contexts:
        - Python: Checks if source_name is 'manual'
        - SQL: Performs a join with EventSource and checks the name
        """
        # Python implementation relies on source_name property, which checks loading
        return self.source_name.lower() == "manual"

    @is_manual.expression
    def is_manual(cls):  # noqa: N805
        """SQL expression for is_manual."""
        from sologm.models.event_source import EventSource

        return (
            select(1)
            .where(
                (EventSource.id == cls.source_id) & (EventSource.name.ilike("manual"))
            )
            .exists()
        ).label("is_manual")

    @hybrid_property
    def is_oracle_generated(self) -> bool:
        """Check if this event was generated by an oracle.

        Works in both Python and SQL contexts:
        - Python: Checks if source_name is 'oracle'
        - SQL: Performs a join with EventSource and checks the name
        """
        # Python implementation relies on source_name property
        return self.source_name.lower() == "oracle"

    @is_oracle_generated.expression
    def is_oracle_generated(cls):  # noqa: N805
        """SQL expression for is_oracle_generated."""
        from sologm.models.event_source import EventSource

        return (
            select(1)
            .where(
                (EventSource.id == cls.source_id) & (EventSource.name.ilike("oracle"))
            )
            .exists()
        ).label("is_oracle_generated")

    @hybrid_property
    def is_dice_generated(self) -> bool:
        """Check if this event was generated by a dice roll.

        Works in both Python and SQL contexts:
        - Python: Checks if source_name is 'dice'
        - SQL: Performs a join with EventSource and checks the name
        """
        # Python implementation relies on source_name property
        return self.source_name.lower() == "dice"

    @is_dice_generated.expression
    def is_dice_generated(cls):  # noqa: N805
        """SQL expression for is_dice_generated."""
        from sologm.models.event_source import EventSource

        return (
            select(1)
            .where((EventSource.id == cls.source_id) & (EventSource.name.ilike("dice")))
            .exists()
        ).label("is_dice_generated")

    @property
    def short_description(self) -> str:
        """Get a shortened version of the description.

        This property provides a convenient way to get a preview of the description.
        """
        max_length = 50
        if len(self.description) <= max_length:
            return self.description
        return self.description[:max_length] + "..."

    @classmethod
    def create(
        cls,
        scene_id: str,
        description: str,
        source_id: int,
        interpretation_id: Optional[str] = None,
    ) -> "Event":
        """Create a new event.

        Args:
            scene_id: ID of the scene this event belongs to.
            description: Description of the event.
            source_id: ID of the event source.
            interpretation_id: Optional ID of the interpretation that created
                               this event.
        Returns:
            A new Event instance.
        """
        return cls(
            id=str(uuid.uuid4()),
            scene_id=scene_id,
            description=description,
            source_id=source_id,
            interpretation_id=interpretation_id,
        )
