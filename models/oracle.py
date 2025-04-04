"""Oracle interpretation models for SoloGM."""

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from sologm.models.base import Base, TimestampMixin

class InterpretationSet(Base, TimestampMixin):
    """SQLAlchemy model representing a set of oracle interpretations."""
    
    __tablename__ = "interpretation_sets"
    
    id = Column(String, primary_key=True)
    scene_id = Column(String, ForeignKey("scenes.id"), nullable=False)
    context = Column(Text, nullable=False)
    oracle_results = Column(Text, nullable=False)
    retry_attempt = Column(Integer, default=0)
    
    # Flag for current interpretation set in a game
    is_current = Column(Boolean, default=False)
    
    # Relationships will be defined in __init__.py

class Interpretation(Base, TimestampMixin):
    """SQLAlchemy model representing a single oracle interpretation."""
    
    __tablename__ = "interpretations"
    
    id = Column(String, primary_key=True)
    set_id = Column(String, ForeignKey("interpretation_sets.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    is_selected = Column(Boolean, default=False)
    
    # Relationships will be defined in __init__.py
