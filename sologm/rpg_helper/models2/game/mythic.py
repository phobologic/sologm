"""
Mythic GME game model.
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple
import random
from enum import Enum
from datetime import datetime

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import object_session

from sologm.rpg_helper.utils.logging import get_logger
from sologm.rpg_helper.models2.base import get_session, close_session
from sologm.rpg_helper.models2.game.base import Game, GameType
from sologm.rpg_helper.models2.game.errors import GameError

logger = get_logger()

class MythicChaosFactor(int, Enum):
    """Chaos factor for Mythic GME."""
    MIN = 1
    LOW = 3
    AVERAGE = 5
    HIGH = 7
    MAX = 9


class ChaosBoundaryError(GameError):
    """Exception raised when attempting to set chaos factor outside valid bounds."""
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
    
    Extends the base Game model with Mythic GME specific functionality.
    """
    __mapper_args__ = {
        'polymorphic_identity': GameType.MYTHIC_GME.value
    }
    
    # Additional columns for Mythic GME
    chaos_factor = Column(Integer, nullable=False, default=MythicChaosFactor.AVERAGE.value)
    scene_count = Column(Integer, nullable=False, default=0)
    
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
    
    def _validate_chaos_factor(self, value: int, raise_error: bool = True) -> bool:
        """
        Validate that a chaos factor is within bounds.
        
        Args:
            value: The chaos factor to validate
            raise_error: Whether to raise an error if invalid
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ChaosBoundaryError: If raise_error is True and value is invalid
        """
        valid = MythicChaosFactor.MIN.value <= value <= MythicChaosFactor.MAX.value
        
        if not valid and raise_error:
            raise ChaosBoundaryError(
                current=self.chaos_factor,
                attempted=value
            )
            
        return valid
    
    def _update_chaos_factor(self, new_value: int) -> int:
        """
        Update the chaos factor and save changes.
        
        Args:
            new_value: The new chaos factor value
            
        Returns:
            The new chaos factor
        """
        self._validate_chaos_factor(new_value)
        old_chaos = self.chaos_factor
        self.chaos_factor = new_value
        self.updated_at = datetime.now()
        
        logger.info(
            "Updated chaos factor",
            game_id=self.id,
            old_chaos=old_chaos,
            new_chaos=self.chaos_factor
        )
        
        # Save changes if the game is already in a session
        session = object_session(self)
        if session:
            session.commit()
            
        return self.chaos_factor
    
    def increase_chaos(self) -> int:
        """
        Increase the chaos factor.
        
        Returns:
            The new chaos factor
            
        Raises:
            ChaosBoundaryError: If already at maximum
        """
        new_value = self.chaos_factor + 1
      
        return self._update_chaos_factor(new_value)
    
    def decrease_chaos(self) -> int:
        """
        Decrease the chaos factor.
        
        Returns:
            The new chaos factor
            
        Raises:
            ChaosBoundaryError: If already at minimum
        """
        new_value = self.chaos_factor - 1
        
        return self._update_chaos_factor(new_value)
    
    def set_chaos_factor(self, chaos_factor: int) -> int:
        """
        Set the chaos factor.
        
        Args:
            chaos_factor: The new chaos factor
            
        Returns:
            The new chaos factor
            
        Raises:
            ChaosBoundaryError: If value is outside valid range
        """
        return self._update_chaos_factor(chaos_factor)
   
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        
        # Add Mythic GME specific fields
        data['chaos_factor'] = self.chaos_factor
        data['scene_count'] = self.scene_count
        
        return data


# Register the MythicGame class with the Game class
Game.register_game_type(GameType.MYTHIC_GME.value, MythicGame) 