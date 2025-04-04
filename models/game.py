"""Game model for SoloGM."""

from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.orm import relationship

from sologm.models.base import Base, TimestampMixin

class Game(Base, TimestampMixin):
    """SQLAlchemy model representing a game in the system."""
    
    __tablename__ = "games"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=False)
    
    # Relationships will be defined in __init__.py
