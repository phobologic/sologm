"""
Game commands for the RPG Helper bot.
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from sologm.rpg_helper.models import (
    Game, GameType, MythicGame, User,
    GameError, ChannelGameExistsError
)
from sologm.rpg_helper.models.init_db import init_db
from sologm.rpg_helper.utils.logging import get_logger

# Initialize the database at module load time
init_db()

logger = get_logger()

def create_game_command(
    channel_id: str,
    workspace_id: str,
    name: str,
    description: str = "",
    game_type: str = "standard",
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    user_display_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new game.
    
    Args:
        channel_id: The channel ID
        workspace_id: The workspace ID
        name: The name of the game
        description: The description of the game
        game_type: The type of game (standard, mythic)
        user_id: The ID of the user creating the game
        user_name: The username of the user creating the game
        user_display_name: The display name of the user creating the game
        
    Returns:
        The created game as a dictionary
        
    Raises:
        ChannelGameExistsError: If a game already exists in the channel
    """
    logger.info(
        "Creating game",
        channel_id=channel_id,
        workspace_id=workspace_id,
        name=name,
        game_type=game_type
    )
    
    # Check if a game already exists in the channel
    session = init_db()[1]()
    try:
        existing_game = session.query(Game).filter_by(
            channel_id=channel_id,
            workspace_id=workspace_id
        ).first()
        
        if existing_game:
            raise ChannelGameExistsError(
                channel_id=channel_id,
                existing_game=existing_game
            )
        
        # Create the game
        if game_type.lower() == "mythic":
            game = MythicGame(
                name=name,
                description=description,
                channel_id=channel_id,
                workspace_id=workspace_id
            )
        else:
            game = Game(
                name=name,
                description=description,
                channel_id=channel_id,
                workspace_id=workspace_id
            )
        
        # Add the user as a member if provided
        if user_id:
            # Get or create the user
            user = session.query(User).filter_by(id=user_id).first()
            if not user:
                user = User(
                    id=user_id,
                    username=user_name or user_id,
                    display_name=user_display_name or user_name or user_id
                )
                session.add(user)
            
            # Add the user to the game
            game.members.append(user)
        
        # Save the game
        session.add(game)
        session.commit()
        
        logger.info(
            "Game created",
            game_id=game.id,
            name=game.name
        )
        
        return game.to_dict()
    finally:
        session.close()

def get_game_in_channel(channel_id: str, workspace_id: str) -> Optional[Game]:
    """
    Get the game in a channel.
    
    Args:
        channel_id: The channel ID
        workspace_id: The workspace ID
        
    Returns:
        The game, or None if not found
    """
    session = init_db()[1]()
    try:
        return session.query(Game).filter_by(
            channel_id=channel_id,
            workspace_id=workspace_id
        ).first()
    finally:
        session.close()

def get_active_game_for_user(user_id: str) -> List[Game]:
    """
    Get all active games for a user.
    
    Args:
        user_id: The user ID
        
    Returns:
        List of active games
    """
    session = init_db()[1]()
    try:
        # Get the user
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return []
        
        # Get active games where the user is a member
        return [game for game in user.games if game.is_active]
    finally:
        session.close()

def delete_game_command(game_id: str) -> Dict[str, Any]:
    """
    Delete a game.
    
    Args:
        game_id: The game ID
        
    Returns:
        The deleted game as a dictionary
        
    Raises:
        NotFoundError: If the game is not found
    """
    session = init_db()[1]()
    try:
        # Get the game
        game = session.query(Game).filter_by(id=game_id).first()
        if not game:
            raise Game.NotFoundError(f"Game with ID {game_id} not found")
        
        # Store the game data before deletion
        game_data = game.to_dict()
        
        # Delete the game
        session.delete(game)
        session.commit()
        
        logger.info(
            "Game deleted",
            game_id=game_id,
            name=game_data.get("name")
        )
        
        return game_data
    finally:
        session.close()

# Additional helper functions as needed 