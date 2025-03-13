"""
Factory for creating game service instances.
"""
from typing import Union

from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.models.game.constants import GameType
from sologm.rpg_helper.services.game.game_service import GameService
from sologm.rpg_helper.services.game.mythic_game_service import MythicGameService
from sologm.rpg_helper.db.config import get_session, close_session
from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger()

class ServiceFactory:
    """Factory for creating appropriate game service instances."""
    
    @staticmethod
    def create_game_service(game: Union[Game, str]) -> GameService:
        """
        Create the appropriate game service for a game.
        
        Args:
            game: Either a Game instance or a game ID
            
        Returns:
            The appropriate service instance
            
        Raises:
            ValueError: If the game is not found
        """
        # If game is a string, assume it's a game ID
        if isinstance(game, str):
            session = get_session()
            try:
                game = session.query(Game).filter_by(id=game).first()
                if not game:
                    raise ValueError(f"Game with ID {game} not found")
            finally:
                close_session(session)
        
        # Create the appropriate service based on game type
        if game.game_type == GameType.MYTHIC:
            logger.debug(
                "Creating MythicGameService",
                game_id=game.id,
                game_type=game.game_type
            )
            return MythicGameService(game)
        else:
            logger.debug(
                "Creating GameService",
                game_id=game.id,
                game_type=game.game_type
            )
            return GameService(game) 