"""Dice roll model for SoloGM."""

import json

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.types import TypeDecorator

from sologm.models.base import Base, TimestampMixin

class JSONType(TypeDecorator):
    """Enables JSON storage by serializing on write and deserializing on read."""
    impl = String

    def process_bind_param(self, value, _):
        """Convert Python object to JSON string for storage."""
        return json.dumps(value) if value is not None else None

    def process_result_value(self, value, _):
        """Convert stored JSON string back to Python object."""
        return json.loads(value) if value else None

class DiceRoll(Base, TimestampMixin):
    """SQLAlchemy model representing a dice roll result."""

    __tablename__ = "dice_rolls"
    id = Column(String, primary_key=True)
    notation = Column(String, nullable=False)
    individual_results = Column(JSONType, nullable=False)  # Store as JSON array
    modifier = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)

    # Optional link to game and scene
    game_id = Column(String, ForeignKey("games.id"), nullable=True)
    scene_id = Column(String, ForeignKey("scenes.id"), nullable=True)

    # Relationships will be defined in __init__.py
