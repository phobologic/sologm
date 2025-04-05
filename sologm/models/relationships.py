"""Relationship definitions for SQLAlchemy models."""

from sqlalchemy.orm import relationship

from sologm.models.dice import DiceRoll
from sologm.models.event import Event
from sologm.models.game import Game
from sologm.models.oracle import Interpretation, InterpretationSet
from sologm.models.scene import Scene

# Game relationships
Game.scenes = relationship("Scene", back_populates="game", cascade="all, delete-orphan")

# Scene relationships
Scene.game = relationship("Game", back_populates="scenes")
Scene.events = relationship(
    "Event", back_populates="scene", cascade="all, delete-orphan"
)
Scene.interpretation_sets = relationship(
    "InterpretationSet", back_populates="scene", cascade="all, delete-orphan"
)
Scene.dice_rolls = relationship("DiceRoll", back_populates="scene")

# Event relationships
Event.scene = relationship("Scene", back_populates="events")
Event.interpretation = relationship("Interpretation", back_populates="events")

# InterpretationSet relationships
InterpretationSet.scene = relationship("Scene", back_populates="interpretation_sets")
InterpretationSet.interpretations = relationship(
    "Interpretation", back_populates="interpretation_set", cascade="all, delete-orphan"
)

# Interpretation relationships
Interpretation.interpretation_set = relationship(
    "InterpretationSet", back_populates="interpretations"
)
Interpretation.events = relationship("Event", back_populates="interpretation")
Interpretation.events = relationship("Event", back_populates="interpretation")

# DiceRoll relationships
DiceRoll.scene = relationship("Scene", back_populates="dice_rolls")
