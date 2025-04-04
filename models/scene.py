"""Scene model for SoloGM."""

import enum
from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship

from sologm.models.base import Base, TimestampMixin

class SceneStatus(enum.Enum):
    """Enumeration of possible scene statuses."""
    ACTIVE = "active"
    COMPLETED = "completed"

class Scene(Base, TimestampMixin):
    """SQLAlchemy model representing a scene in a game."""
    
    __tablename__ = "scenes"
    
    id = Column(String, primary_key=True)
    game_id = Column(String, ForeignKey("games.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(Enum(SceneStatus), nullable=False, default=SceneStatus.ACTIVE)
    sequence = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=False)
    
    # Relationships will be defined in __init__.py
