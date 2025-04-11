"""Dice roll model for SoloGM."""

import json
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from sologm.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from sologm.models.act import Act
    from sologm.models.game import Game
    from sologm.models.scene import Scene


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
        ForeignKey("scenes.id"), nullable=True
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
