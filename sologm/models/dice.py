"""Dice roll model for SoloGM."""

import json
import uuid
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.types import TypeDecorator

from sologm.models.base import Base, TimestampMixin


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
    id: Column = Column(String(36), primary_key=True,
                        default=lambda: str(uuid.uuid4()))
    notation: Column = Column(String, nullable=False)
    individual_results: Column = Column(JSONType, nullable=False)  # Store as JSON array
    modifier: Column = Column(Integer, nullable=False)
    total: Column = Column(Integer, nullable=False)
    reason: Column = Column(Text, nullable=True)

    # Optional link to game and scene
    scene_id: Column = Column(String, ForeignKey("scenes.id"), nullable=True)

    # Relationships will be defined in __init__.py

    @classmethod
    def create(
        cls,
        notation: str,
        individual_results: List[int],
        modifier: int,
        total: int,
        reason: Optional[str] = None,
        scene_id: Optional[str] = None
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
            scene_id=scene_id
        )
