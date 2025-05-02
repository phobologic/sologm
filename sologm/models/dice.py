"""Dice roll model for SoloGM."""

import json
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from sologm.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from sologm.models.act import Act
    from sologm.models.game import Game


class JSONType(TypeDecorator):
    """Enables JSON storage by serializing on write and deserializing on read."""

    impl = String

    def process_bind_param(
        self, value: Optional[Union[Dict[str, Any], List[Any]]], _: Any
    ) -> Optional[str]:
        """Convert Python object to JSON string for storage."""
        return json.dumps(value) if value is not None else None

    def process_result_value(
        self, value: Optional[str], _: Any
    ) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """Convert stored JSON string back to Python object."""
        return json.loads(value) if value else None


class DiceRoll(Base, TimestampMixin):
    """SQLAlchemy model representing a dice roll result."""

    __tablename__ = "dice_rolls"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid.uuid4()))
    notation: Mapped[str] = mapped_column(nullable=False)
    # Store as JSON array
    individual_results: Mapped[List[int]] = mapped_column(JSONType, nullable=False)
    modifier: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Optional link to game and scene
    scene_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"), nullable=True
    )

    # Relationships will be defined in relationships.py

    @property
    def act(self) -> Optional["Act"]:
        """Get the act this dice roll belongs to, if any."""
        return self.scene.act if self.scene else None

    @property
    def act_id(self) -> Optional[str]:
        """Get the act ID this dice roll belongs to, if any."""
        return self.scene.act_id if self.scene else None

    @property
    def game(self) -> Optional["Game"]:
        """Get the game this dice roll belongs to, if any."""
        return self.scene.act.game if self.scene else None

    @property
    def game_id(self) -> Optional[str]:
        """Get the game ID this dice roll belongs to, if any."""
        return self.scene.act.game_id if self.scene else None

    @property
    def formatted_results(self) -> str:
        """Get a formatted string representation of the dice roll results.

        This property provides a human-readable format of the dice roll.
        Example: "2d6+3: [2, 5] + 3 = 10"
        """
        dice_part = f"{self.notation}"
        results_part = f"{self.individual_results}"

        if self.modifier != 0:
            modifier_sign = "+" if self.modifier > 0 else ""
            modifier_part = f" {modifier_sign}{self.modifier}"
        else:
            modifier_part = ""

        return f"{dice_part}: {results_part}{modifier_part} = {self.total}"

    @property
    def short_reason(self) -> Optional[str]:
        """Get a shortened version of the reason, if any.

        This property provides a convenient way to get a preview of the reason.
        """
        if not self.reason:
            return None

        max_length = 30
        if len(self.reason) <= max_length:
            return self.reason
        return self.reason[:max_length] + "..."

    @hybrid_property
    def has_reason(self) -> bool:
        """Check if this dice roll has a reason.

        Works in both Python and SQL contexts:
        - Python: Checks if reason is not None and not empty
        - SQL: Performs a direct column comparison
        """
        return self.reason is not None and self.reason.strip() != ""

    @has_reason.expression
    def has_reason(cls):  # noqa: N805
        """SQL expression for has_reason."""
        return ((cls.reason is not None) & (cls.reason != "")).label("has_reason")

    @classmethod
    def create(
        cls,
        notation: str,
        individual_results: List[int],
        modifier: int,
        total: int,
        reason: Optional[str] = None,
        scene_id: Optional[str] = None,
    ) -> "DiceRoll":
        """Create a new dice roll record.

        Args:
            notation: The dice notation (e.g., "2d6+3").
            individual_results: List of individual die results.
            modifier: The modifier applied to the roll.
            total: The total result of the roll.
            reason: Optional reason for the roll.
            scene_id: Optional ID of the scene this roll belongs to.
        Returns:
            A new DiceRoll instance.
        """
        return cls(
            id=str(uuid.uuid4()),
            notation=notation,
            individual_results=individual_results,
            modifier=modifier,
            total=total,
            reason=reason,
            scene_id=scene_id,
        )
