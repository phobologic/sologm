"""Game model for SoloGM."""

import uuid
from typing import TYPE_CHECKING, Dict, List, Optional

from sqlalchemy import Text, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from sologm.models.base import Base, TimestampMixin
from sologm.models.mixins import (
    CountingMixin,
    DirectCountConfig,
    ExistenceCheckMixin,
    ExistenceConfig,
    FilteredRelationshipStatusConfig,
    StatusCheckMixin,
)
from sologm.models.utils import (
    aggregate_cross_relationship_collection,
    get_active_entity,
    get_filtered_collection,
    get_latest_entity,
    slugify,
)

if TYPE_CHECKING:
    from sologm.models.act import Act
    from sologm.models.scene import Scene

    # Properties generated by ExistenceCheckMixin
    has_acts: bool

    # Properties generated by CountingMixin
    act_count: int

    # Properties generated by StatusCheckMixin
    has_active_act: bool


class Game(ExistenceCheckMixin, CountingMixin, StatusCheckMixin, Base, TimestampMixin):
    """SQLAlchemy model representing a game in the system."""

    __tablename__ = "games"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=False)

    # Relationships this model owns
    acts: Mapped[List["Act"]] = relationship(
        "Act", back_populates="game", cascade="all, delete-orphan"
    )

    # Configuration for ExistenceCheckMixin to generate has_X properties
    # Import locally to avoid circular import issues
    @staticmethod
    def _get_existence_configs() -> Dict:
        from sologm.models.act import Act

        return {
            "acts": ExistenceConfig(model=Act, foreign_key="game_id"),
        }

    _existence_configs = _get_existence_configs()

    # Configuration for CountingMixin to generate X_count properties
    # Import locally to avoid circular import issues
    @staticmethod
    def _get_counting_configs() -> Dict:
        from sologm.models.act import Act

        return {
            "act": DirectCountConfig(
                model=Act, foreign_key="game_id", relationship_name="acts"
            ),
        }

    _counting_configs = _get_counting_configs()

    # Configuration for StatusCheckMixin to generate status properties
    # Import locally to avoid circular import issues
    @staticmethod
    def _get_status_configs() -> Dict:
        from sologm.models.act import Act

        return {
            "act": FilteredRelationshipStatusConfig(
                model=Act,
                foreign_key="game_id",
                filter_field="is_active",
                filter_value=True,
                relationship_name="acts",
            ),
            # Note: has_active_scene requires complex cross-table filtering
            # (both act and scene active) - too complex for current StatusCheckMixin
            # and remains manually implemented
            # Note: has_completed_acts is broken because Act model doesn't have
            # status field
        }

    _status_configs = _get_status_configs()

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

    # --- Hybrid Properties (for efficient querying) ---
    #
    # Note: has_acts is now generated by ExistenceCheckMixin via _existence_configs.
    # The complex properties has_active_act, has_active_scene, and has_completed_acts
    # will be migrated when the mixin supports filtering conditions and JOIN operations.

    # has_acts property is now generated by ExistenceCheckMixin

    # act_count property is now generated by CountingMixin

    @property
    def active_act(self) -> Optional["Act"]:
        """Get the active act for this game, if any.

        This property filters the already loaded acts collection
        and doesn't trigger a new database query.
        """
        return get_active_entity(self.acts)

    # has_active_act property is now generated by StatusCheckMixin

    @property
    def active_scene(self) -> Optional["Scene"]:
        """Get the active scene for this game, if any.

        This property navigates through the active act to find
        the active scene, without triggering new database queries.
        """
        active_act = get_active_entity(self.acts)
        if active_act:
            return get_active_entity(active_act.scenes)
        return None

    @hybrid_property
    def has_active_scene(self) -> bool:
        """Check if the game has an active scene.

        Works in both Python and SQL contexts:
        - Python: Checks if active_scene is not None
        - SQL: Performs a subquery to check for active scenes

        Note: Requires both act and scene to be active, which is too complex
        for the current StatusCheckMixin implementation.
        """
        return self.active_scene is not None

    @has_active_scene.expression
    def has_active_scene(cls):  # noqa: N805
        """SQL expression for has_active_scene."""
        from sologm.models.act import Act
        from sologm.models.scene import Scene

        return (
            select(1)
            .where(
                (Act.game_id == cls.id)
                & Act.is_active
                & (Scene.act_id == Act.id)
                & Scene.is_active
            )
            .exists()
            .label("has_active_scene")
        )

    # completed_acts property removed - Act model doesn't have status field
    # TODO: Add back when Act model gets status field and ActStatus enum

    # has_completed_acts property removed - Act model doesn't have status field
    # This property was broken due to missing ActStatus enum

    @property
    def active_acts(self) -> List["Act"]:
        """Get all active acts for this game.

        This property filters the already loaded acts collection
        and doesn't trigger a new database query.
        """
        return get_filtered_collection(self.acts, "is_active", True)

    @property
    def latest_act(self) -> Optional["Act"]:
        """Get the most recently created act for this game, if any.

        This property sorts the already loaded acts collection
        and doesn't trigger a new database query.
        """
        return get_latest_entity(self.acts)

    @property
    def latest_scene(self) -> Optional["Scene"]:
        """Get the most recently created scene for this game, if any.

        This property navigates through all acts to find the latest scene,
        without triggering new database queries.
        """
        all_scenes = aggregate_cross_relationship_collection(self, ["acts", "scenes"])
        return get_latest_entity(all_scenes)

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
