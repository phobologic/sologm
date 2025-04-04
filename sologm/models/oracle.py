"""Oracle interpretation models for SoloGM."""

import uuid
from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text

from sologm.models.base import Base, TimestampMixin


class InterpretationSet(Base, TimestampMixin):
    """SQLAlchemy model representing a set of oracle interpretations."""

    __tablename__ = "interpretation_sets"
    id: Column = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scene_id: Column = Column(String, ForeignKey("scenes.id"), nullable=False)
    context: Column = Column(Text, nullable=False)
    oracle_results: Column = Column(Text, nullable=False)
    retry_attempt: Column = Column(Integer, default=0)

    # Flag for current interpretation set in a game
    is_current: Column = Column(Boolean, default=False)

    # Relationships will be defined in __init__.py

    @classmethod
    def create(
        cls,
        scene_id: str,
        context: str,
        oracle_results: str,
        retry_attempt: int = 0,
        is_current: bool = False
    ) -> "InterpretationSet":
        """Create a new interpretation set.

        Args:
            scene_id: ID of the scene this interpretation set belongs to.
            context: Context for the interpretation.
            oracle_results: Raw oracle results.
            retry_attempt: Number of retry attempts.
            is_current: Whether this is the current interpretation set.
        Returns:
            A new InterpretationSet instance.
        """
        return cls(
            id=str(uuid.uuid4()),
            scene_id=scene_id,
            context=context,
            oracle_results=oracle_results,
            retry_attempt=retry_attempt,
            is_current=is_current
        )

class Interpretation(Base, TimestampMixin):
    """SQLAlchemy model representing a single oracle interpretation."""

    __tablename__ = "interpretations"
    id: Column = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    set_id: Column = Column(String, ForeignKey("interpretation_sets.id"), nullable=False)
    title: Column = Column(String, nullable=False)
    description: Column = Column(Text, nullable=False)
    is_selected: Column = Column(Boolean, default=False)

    # Relationships will be defined in __init__.py

    @classmethod
    def create(
        cls,
        set_id: str,
        title: str,
        description: str,
        is_selected: bool = False
    ) -> "Interpretation":
        """Create a new interpretation.

        Args:
            set_id: ID of the interpretation set this interpretation belongs to.
            title: Title of the interpretation.
            description: Description of the interpretation.
            is_selected: Whether this interpretation is selected.
        Returns:
            A new Interpretation instance.
        """
        return cls(
            id=str(uuid.uuid4()),
            set_id=set_id,
            title=title,
            description=description,
            is_selected=is_selected
        )
