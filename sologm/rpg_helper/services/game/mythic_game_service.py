"""
Mythic GME game service for managing Mythic GME game operations.
"""
from typing import Dict, Any, Optional, Tuple, List, Union
import random
import enum
from datetime import datetime

from sqlalchemy.orm import object_session

from sologm.rpg_helper.models.game.mythic import (
    MythicGame, MythicChaosFactor, ChaosBoundaryError
)
from sologm.rpg_helper.models.scene_event import SceneEvent
from sologm.rpg_helper.services.game.game_service import GameService
from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger()

class MythicGameService(GameService):
    """Service for managing Mythic GME game operations."""
    
    @property
    def mythic_game(self) -> MythicGame:
        """Get the game as a MythicGame."""
        return self.game
    
    def increase_chaos(self) -> int:
        """
        Increase the chaos factor.
        
        Returns:
            The new chaos factor
            
        Raises:
            ChaosBoundaryError: If already at maximum
        """
        new_value = self.mythic_game.chaos_factor + 1
        
        if new_value > MythicChaosFactor.MAX.value:
            raise ChaosBoundaryError(
                current=self.mythic_game.chaos_factor,
                attempted=new_value
            )
        
        self.mythic_game.chaos_factor = new_value
        self.mythic_game.updated_at = datetime.now()
        
        # Save changes if the game is already in a session
        session = object_session(self.mythic_game)
        if session:
            session.commit()
            
        logger.info(
            "Increased chaos factor",
            game_id=self.mythic_game.id,
            old_chaos=self.mythic_game.chaos_factor - 1,
            new_chaos=self.mythic_game.chaos_factor
        )
        
        return self.mythic_game.chaos_factor
    
    def decrease_chaos(self) -> int:
        """
        Decrease the chaos factor.
        
        Returns:
            The new chaos factor
            
        Raises:
            ChaosBoundaryError: If already at minimum
        """
        new_value = self.mythic_game.chaos_factor - 1
        
        if new_value < MythicChaosFactor.MIN.value:
            raise ChaosBoundaryError(
                current=self.mythic_game.chaos_factor,
                attempted=new_value
            )
        
        self.mythic_game.chaos_factor = new_value
        self.mythic_game.updated_at = datetime.now()
        
        # Save changes if the game is already in a session
        session = object_session(self.mythic_game)
        if session:
            session.commit()
            
        logger.info(
            "Decreased chaos factor",
            game_id=self.mythic_game.id,
            old_chaos=self.mythic_game.chaos_factor + 1,
            new_chaos=self.mythic_game.chaos_factor
        )
        
        return self.mythic_game.chaos_factor
    
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
        if not MythicChaosFactor.MIN.value <= chaos_factor <= MythicChaosFactor.MAX.value:
            raise ChaosBoundaryError(
                current=self.mythic_game.chaos_factor,
                attempted=chaos_factor
            )
        
        old_chaos = self.mythic_game.chaos_factor
        self.mythic_game.chaos_factor = chaos_factor
        self.mythic_game.updated_at = datetime.now()
        
        # Save changes if the game is already in a session
        session = object_session(self.mythic_game)
        if session:
            session.commit()
            
        logger.info(
            "Set chaos factor",
            game_id=self.mythic_game.id,
            old_chaos=old_chaos,
            new_chaos=self.mythic_game.chaos_factor
        )
        
        return self.mythic_game.chaos_factor 