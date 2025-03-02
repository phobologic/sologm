"""
Game-related exceptions.
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Game

class GameError(Exception):
    """Base exception for game-related errors."""
    pass

class ChannelGameExistsError(GameError):
    """Exception raised when attempting to create a game in a channel that already has one."""
    def __init__(self, channel_id: str, existing_game: 'Game'):
        self.channel_id = channel_id
        self.existing_game = existing_game
        super().__init__(f"A game already exists in channel {channel_id}") 