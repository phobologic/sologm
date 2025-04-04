"""Event model for SoloGM."""

from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from sologm.models.base import Base, TimestampMixin

class Event(Base, TimestampMixin):
    """SQLAlchemy model representing a game event."""
    
    __tablename__ = "events"
    
    id = Column(String, primary_key=True)
    scene_id = Column(String, ForeignKey("scenes.id"), nullable=False)
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    description = Column(Text, nullable=False)
    source = Column(String, nullable=False)  # manual, oracle, dice
    
    # Optional link to interpretation if this event was created from one
    interpretation_id = Column(String, ForeignKey("interpretations.id"), nullable=True)
    
    # Relationships will be defined in __init__.py
