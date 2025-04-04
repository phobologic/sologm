"""Dice roll model for SoloGM."""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from sologm.models.base import Base, TimestampMixin

class DiceRoll(Base, TimestampMixin):
    """SQLAlchemy model representing a dice roll result."""
    
    __tablename__ = "dice_rolls"
    
    id = Column(String, primary_key=True)
    notation = Column(String, nullable=False)
    individual_results = Column(JSON, nullable=False)  # Store as JSON array
    modifier = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    reason = Column(Text, nullable=True)
    
    # Optional link to game and scene
    game_id = Column(String, ForeignKey("games.id"), nullable=True)
    scene_id = Column(String, ForeignKey("scenes.id"), nullable=True)
    
    # Relationships will be defined in __init__.py
