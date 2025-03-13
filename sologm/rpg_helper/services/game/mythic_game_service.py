"""
Mythic GME game service for managing Mythic GME game operations.
"""
from typing import Dict, Any, Optional, Tuple, List, Union
import random
from datetime import datetime

from sqlalchemy.orm import object_session

from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.models.game.constants import (
    GameType, MythicChaosFactor, ChaosBoundaryError
)
from sologm.rpg_helper.models.scene_event import SceneEvent
from sologm.rpg_helper.services.game.game_service import GameService
from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger()

class MythicGameService(GameService):
    """Service for managing Mythic GME game operations."""
    
    # Constants for settings keys
    SETTING_CHAOS_FACTOR = "chaos_factor"
    
    def __init__(self, game: Game):
        """Initialize with a game instance."""
        super().__init__(game)
        if game.game_type != GameType.MYTHIC:
            raise ValueError(f"Game {game.id} is not a Mythic game")
    
    def get_chaos_factor(self) -> int:
        """
        Get the chaos factor.
        
        Returns:
            The chaos factor
        """
        return int(self.game.get_setting(
            self.SETTING_CHAOS_FACTOR, 
            MythicChaosFactor.AVERAGE
        ))
    
    def increase_chaos(self) -> int:
        """
        Increase the chaos factor.
        
        Returns:
            The new chaos factor
            
        Raises:
            ChaosBoundaryError: If already at maximum
        """
        current = self.get_chaos_factor()
        new_value = current + 1
        
        if new_value > MythicChaosFactor.MAX:
            raise ChaosBoundaryError(
                current=current,
                attempted=new_value
            )
        
        self.set_chaos_factor(new_value)
        
        logger.info(
            "Increased chaos factor",
            game_id=self.game.id,
            old_chaos=current,
            new_chaos=new_value
        )
        
        return new_value
    
    def decrease_chaos(self) -> int:
        """
        Decrease the chaos factor.
        
        Returns:
            The new chaos factor
            
        Raises:
            ChaosBoundaryError: If already at minimum
        """
        current = self.get_chaos_factor()
        new_value = current - 1
        
        if new_value < MythicChaosFactor.MIN:
            raise ChaosBoundaryError(
                current=current,
                attempted=new_value
            )
        
        self.set_chaos_factor(new_value)
        
        logger.info(
            "Decreased chaos factor",
            game_id=self.game.id,
            old_chaos=current,
            new_chaos=new_value
        )
        
        return new_value
    
    def set_chaos_factor(self, value: int) -> int:
        """
        Set the chaos factor.
        
        Args:
            value: The new chaos factor
            
        Returns:
            The new chaos factor
            
        Raises:
            ChaosBoundaryError: If value is outside valid range
        """
        current = self.get_chaos_factor()
        
        if not MythicChaosFactor.MIN <= value <= MythicChaosFactor.MAX:
            raise ChaosBoundaryError(
                current=current,
                attempted=value
            )
        
        self.game.set_setting(self.SETTING_CHAOS_FACTOR, value)
        self.game.updated_at = datetime.now()
        
        # Save changes if the game is already in a session
        session = object_session(self.game)
        if session:
            session.commit()
            
        logger.info(
            "Set chaos factor",
            game_id=self.game.id,
            old_chaos=current,
            new_chaos=value
        )
        
        return value 