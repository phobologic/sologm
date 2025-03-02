"""
Game-related functions.
"""
import uuid
from typing import Optional, TYPE_CHECKING

from .base import Game
from .mythic import MythicGMEGame
from .errors import ChannelGameExistsError
from .storage import games_by_id, games_by_channel

from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger()

def create_game(
    name: str,
    creator_id: str,
    channel_id: str,
    game_type: str = "standard",
    **kwargs
) -> Game:
    """
    Create a new game.
    
    Args:
        name: The name of the game
        creator_id: The ID of the user creating the game
        channel_id: The ID of the channel the game is in
        game_type: The type of game to create (standard or mythic)
        **kwargs: Additional arguments to pass to the game constructor
        
    Returns:
        The created game
        
    Raises:
        ValueError: If the game type is invalid
        ChannelGameExistsError: If a game already exists in the channel
    """
    # Check if a game already exists in this channel
    if channel_id in games_by_channel:
        logger.warning(
            "Attempted to create game in channel with existing game",
            channel_id=channel_id,
            existing_game_id=games_by_channel[channel_id].id
        )
        raise ChannelGameExistsError(channel_id, games_by_channel[channel_id])
    
    # Generate a unique ID
    game_id = str(uuid.uuid4())
    
    # Create the game
    if game_type == "standard":
        game = Game(
            id=game_id,
            name=name,
            creator_id=creator_id,
            channel_id=channel_id,
            **kwargs
        )
    elif game_type == "mythic":
        game = MythicGMEGame(
            id=game_id,
            name=name,
            creator_id=creator_id,
            channel_id=channel_id,
            **kwargs
        )
    else:
        raise ValueError(f"Invalid game type: {game_type}")
    
    # Store the game
    games_by_id[game_id] = game
    games_by_channel[channel_id] = game
    
    logger.info(
        "Created new game",
        game_id=game_id,
        name=name,
        creator_id=creator_id,
        channel_id=channel_id,
        game_type=game_type
    )
    
    return game

def get_game_in_channel(channel_id: str) -> Optional[Game]:
    """
    Get the game in a channel.
    
    Args:
        channel_id: The ID of the channel
        
    Returns:
        The game, or None if no game exists in the channel
    """
    return games_by_channel.get(channel_id)

def get_active_game_for_user(user_id: str, channel_id: str) -> Optional[Game]:
    """
    Get the active game for a user in a channel.
    
    Args:
        user_id: The ID of the user
        channel_id: The ID of the channel
        
    Returns:
        The game, or None if no game exists or the user is not a member
    """
    game = get_game_in_channel(channel_id)
    if game and game.is_member(user_id):
        return game
    return None

def delete_game(game_id: str) -> bool:
    """
    Delete a game.
    
    Args:
        game_id: The ID of the game to delete
        
    Returns:
        True if the game was deleted, False if it wasn't found
    """
    if game_id not in games_by_id:
        return False
    
    game = games_by_id[game_id]
    channel_id = game.channel_id
    
    # Remove from storage
    del games_by_id[game_id]
    if channel_id in games_by_channel:
        del games_by_channel[channel_id]
    
    logger.info(
        "Deleted game",
        game_id=game_id,
        channel_id=channel_id
    )
    
    return True 