"""
Game models package.
"""
# Re-export everything for backward compatibility
from .base import Game, GameSettings
from .mythic import MythicGMEGame
from .errors import GameError, ChannelGameExistsError
from .functions import (
    create_game, 
    get_game_in_channel, 
    get_active_game_for_user, 
    delete_game
)
from .storage import games_by_id, games_by_channel

# For type checking
__all__ = [
    'Game',
    'GameSettings',
    'MythicGMEGame',
    'GameError',
    'ChannelGameExistsError',
    'create_game',
    'get_game_in_channel',
    'get_active_game_for_user',
    'delete_game',
    'games_by_id',
    'games_by_channel'
] 