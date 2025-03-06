"""
Mythic GME game model.
"""
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy import Column, Integer, Enum as SQLAlchemyEnum

from sologm.rpg_helper.utils.logging import get_logger
from sologm.rpg_helper.models.game.base import Game, GameType
from sologm.rpg_helper.models.game.errors import GameError

logger = get_logger()

class MythicChaosFactor(int, Enum):
    """Chaos factor for Mythic GME."""
    MIN = 1
    LOW = 3
    AVERAGE = 5
    HIGH = 7
    MAX = 9


class ChaosBoundaryError(GameError):
    """Exception raised when attempting to set chaos factor outside valid range."""
    def __init__(self, attempted: int, current: Optional[int] = None):
        self.attempted = attempted
        self.current = current
        
        if attempted < MythicChaosFactor.MIN.value:
            message = f"Cannot decrease chaos factor below minimum ({MythicChaosFactor.MIN.value}, value provided: {attempted})"
        elif attempted > MythicChaosFactor.MAX.value:
            message = f"Cannot increase chaos factor above maximum ({MythicChaosFactor.MAX.value}, value provided: {attempted})"
        else:
            message = f"Invalid chaos factor: {attempted}"
            
        super().__init__(message)


class MythicGame(Game):
    """
    SQLAlchemy model for Mythic GME games.
    
    Extends the base Game model with Mythic GME specific fields.
    """
    chaos_factor = Column(Integer, nullable=False, default=MythicChaosFactor.AVERAGE.value)
    
    # Polymorphic identity for inheritance
    __mapper_args__ = {
        'polymorphic_identity': GameType.MYTHIC.value
    }
    
    def __init__(self, **kwargs):
        """Initialize a new Mythic GME game."""
        # Set default chaos factor if not provided
        if 'chaos_factor' not in kwargs:
            kwargs['chaos_factor'] = MythicChaosFactor.AVERAGE.value
        else:
            # Validate chaos factor
            chaos = kwargs['chaos_factor']
            if not MythicChaosFactor.MIN.value <= chaos <= MythicChaosFactor.MAX.value:
                # Raise an exception instead of defaulting
                raise ChaosBoundaryError(
                    current=getattr(self, 'chaos_factor', MythicChaosFactor.AVERAGE.value),
                    attempted=chaos
                )
        
        super().__init__(**kwargs)
        
        logger.info(
            "Created new Mythic GME game",
            game_id=self.id,
            chaos_factor=self.chaos_factor
        )
    
    def validate_chaos_factor(self, value: int) -> bool:
        """
        Validate that a chaos factor is within bounds.
        
        Args:
            value: The chaos factor to validate
            
        Returns:
            True if valid
            
        Raises:
            ChaosBoundaryError: If value is invalid
        """
        if not MythicChaosFactor.MIN.value <= value <= MythicChaosFactor.MAX.value:
            raise ChaosBoundaryError(
                current=self.chaos_factor,
                attempted=value
            )
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        
        # Add Mythic GME specific fields
        data['chaos_factor'] = self.chaos_factor
        
        return data


# Register the MythicGame class with the Game class
Game.register_game_type(GameType.MYTHIC.value, MythicGame) 