"""Relationship definitions for SQLAlchemy models."""

from sqlalchemy.orm import relationship

from sologm.models.act import Act
from sologm.models.dice import DiceRoll
from sologm.models.event import Event
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene

# Non-owning relationships only

# Act relationships
Act.game = relationship("Game", back_populates="acts")

# Scene relationships
Scene.act = relationship("Act", back_populates="scenes")

# Event relationships
Event.scene = relationship("Scene", back_populates="events")
Event.interpretation = relationship("Interpretation", back_populates="events")

# InterpretationSet relationships
InterpretationSet.scene = relationship("Scene", back_populates="interpretation_sets")

# Interpretation relationships
Interpretation.interpretation_set = relationship(
    "InterpretationSet", back_populates="interpretations"
)

# DiceRoll relationships
DiceRoll.scene = relationship("Scene", back_populates="dice_rolls")
