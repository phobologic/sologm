"""Game model for SoloGM."""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Text, func, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from sologm.models.base import Base, TimestampMixin
from sologm.models.utils import slugify

if TYPE_CHECKING:
    from sologm.models.act import Act
    from sologm.models.scene import Scene


class Game(Base, TimestampMixin):
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

    @hybrid_property
    def has_acts(self) -> bool:
        """Check if the game has any acts.

        Works in both Python and SQL contexts:
        - Python: Checks if the acts list is non-empty
        - SQL: Performs a subquery to check for acts
        """
        return len(self.acts) > 0

    @has_acts.expression
    def has_acts(cls):  # noqa: N805
        """SQL expression for has_acts."""
        from sologm.models.act import Act

        return select(1).where(Act.game_id == cls.id).exists().label("has_acts")

    @hybrid_property
    def act_count(self) -> int:
        """Get the number of acts in this game.

        Works in both Python and SQL contexts:
        - Python: Returns the length of the acts list
        - SQL: Performs a count query
        """
        return len(self.acts)

    @act_count.expression
    def act_count(cls):  # noqa: N805
        """SQL expression for act_count."""
        from sologm.models.act import Act

        return (
            select(func.count(Act.id)).where(Act.game_id == cls.id).label("act_count")
        )

    @property
    def active_act(self) -> Optional["Act"]:
        """Get the active act for this game, if any.

        This property filters the already loaded acts collection
        and doesn't trigger a new database query.
        """
        for act in self.acts:
            if act.is_active:
                return act
        return None

    @hybrid_property
    def has_active_act(self) -> bool:
        """Check if the game has an active act.

        Works in both Python and SQL contexts:
        - Python: Checks if active_act is not None
        - SQL: Performs a subquery to check for active acts
        """
        return any(act.is_active for act in self.acts)

    @has_active_act.expression
    def has_active_act(cls):  # noqa: N805
        """SQL expression for has_active_act."""
        from sologm.models.act import Act

        return (
            select(1)
            .where((Act.game_id == cls.id) & Act.is_active)
            .exists()
            .label("has_active_act")
        )

    @property
    def active_scene(self) -> Optional["Scene"]:
        """Get the active scene for this game, if any.

        This property navigates through the active act to find
        the active scene, without triggering new database queries.
        """
        active_act = self.active_act
        if active_act:
            for scene in active_act.scenes:
                if scene.is_active:
                    return scene
        return None

    @hybrid_property
    def has_active_scene(self) -> bool:
        """Check if the game has an active scene.

        Works in both Python and SQL contexts:
        - Python: Checks if active_scene is not None
        - SQL: Performs a subquery to check for active scenes
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

    @property
    def completed_acts(self) -> List["Act"]:
        """Get all completed acts for this game.

        This property filters the already loaded acts collection
        and doesn't trigger a new database query.
        """
        from sologm.models.act import ActStatus

        return [act for act in self.acts if act.status == ActStatus.COMPLETED]

    @hybrid_property
    def has_completed_acts(self) -> bool:
        """Check if the game has any completed acts.

        Works in both Python and SQL contexts:
        - Python: Checks if completed_acts is non-empty
        - SQL: Performs a subquery to check for completed acts
        """
        from sologm.models.act import ActStatus

        return any(act.status == ActStatus.COMPLETED for act in self.acts)

    @has_completed_acts.expression
    def has_completed_acts(cls):  # noqa: N805
        """SQL expression for has_completed_acts."""
        from sologm.models.act import Act, ActStatus

        return (
            select(1)
            .where((Act.game_id == cls.id) & (Act.status == ActStatus.COMPLETED))
            .exists()
            .label("has_completed_acts")
        )

    @property
    def active_acts(self) -> List["Act"]:
        """Get all active acts for this game.

        This property filters the already loaded acts collection
        and doesn't trigger a new database query.
        """
        from sologm.models.act import ActStatus

        return [act for act in self.acts if act.status == ActStatus.ACTIVE]

    @property
    def latest_act(self) -> Optional["Act"]:
        """Get the most recently created act for this game, if any.

        This property sorts the already loaded acts collection
        and doesn't trigger a new database query.
        """
        if not self.acts:
            return None
        return sorted(self.acts, key=lambda act: act.created_at, reverse=True)[0]

    @property
    def latest_scene(self) -> Optional["Scene"]:
        """Get the most recently created scene for this game, if any.

        This property navigates through all acts to find the latest scene,
        without triggering new database queries.
        """
        latest_scene = None
        latest_time = None

        for act in self.acts:
            for scene in act.scenes:
                if latest_time is None or scene.created_at > latest_time:
                    latest_scene = scene
                    latest_time = scene.created_at

        return latest_scene

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
