"""
Adapter module to provide backward compatibility with the old models API.
"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

from sologm.rpg_helper.models import (
    Game, GameType, MythicGame, User, Scene, SceneStatus, Poll, PollStatus,
    GameError, ChannelGameExistsError
)
from sologm.rpg_helper.models.init_db import init_db

# Initialize the database
engine, Session = init_db()

# Game functions
def create_game(
    name: str,
    channel_id: str,
    workspace_id: str,
    description: str = "",
    game_type: str = "standard",
    user_id: Optional[str] = None,
    user_name: Optional[str] = None,
    user_display_name: Optional[str] = None
) -> Game:
    """Create a game using the new models."""
    # Check if a game already exists in the channel
    existing_game = get_game_in_channel(channel_id, workspace_id)
    if existing_game:
        raise ChannelGameExistsError(
            f"A game already exists in this channel: {existing_game.name}"
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
        session = Session()
        try:
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
            
            # Add the game to the session
            session.add(game)
            session.commit()
        finally:
            session.close()
    else:
        # Save the game
        session = Session()
        try:
            session.add(game)
            session.commit()
        finally:
            session.close()
    
    return game

def get_game_in_channel(channel_id: str, workspace_id: str) -> Optional[Game]:
    """Get a game in a channel using the new models."""
    session = Session()
    try:
        return session.query(Game).filter_by(
            channel_id=channel_id,
            workspace_id=workspace_id
        ).first()
    finally:
        session.close()

def get_game(game_id: str) -> Optional[Game]:
    """Get a game by ID using the new models."""
    session = Session()
    try:
        return session.query(Game).filter_by(id=game_id).first()
    finally:
        session.close()

def get_active_game_for_user(user_id: str) -> List[Game]:
    """Get active games for a user using the new models."""
    session = Session()
    try:
        # Get the user
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return []
        
        # Get active games where the user is a member
        return [game for game in user.games if game.is_active]
    finally:
        session.close()

def delete_game(game_id: str) -> bool:
    """Delete a game using the new models."""
    session = Session()
    try:
        # Get the game
        game = session.query(Game).filter_by(id=game_id).first()
        if not game:
            return False
        
        # Delete the game
        session.delete(game)
        session.commit()
        return True
    finally:
        session.close()

# Scene functions
def create_scene(
    game_id: str,
    title: str,
    description: str = ""
) -> Optional[Scene]:
    """Create a scene using the new models."""
    session = Session()
    try:
        # Get the game
        game = session.query(Game).filter_by(id=game_id).first()
        if not game:
            return None
        
        # Create the scene
        scene = game.create_scene(
            title=title,
            description=description
        )
        
        # Commit the changes
        session.commit()
        return scene
    finally:
        session.close()

def get_scene(scene_id: str) -> Optional[Scene]:
    """Get a scene by ID using the new models."""
    session = Session()
    try:
        return session.query(Scene).filter_by(id=scene_id).first()
    finally:
        session.close()

def get_scenes_for_game(game_id: str) -> List[Scene]:
    """Get scenes for a game using the new models."""
    session = Session()
    try:
        # Get the game
        game = session.query(Game).filter_by(id=game_id).first()
        if not game:
            return []
        
        # Get the scenes
        return game.get_scenes()
    finally:
        session.close()

def update_scene_status(scene_id: str, status: str) -> bool:
    """Update a scene's status using the new models."""
    session = Session()
    try:
        # Get the scene
        scene = session.query(Scene).filter_by(id=scene_id).first()
        if not scene:
            return False
        
        # Update the status
        try:
            scene.status = SceneStatus(status)
            session.commit()
            return True
        except ValueError:
            return False
    finally:
        session.close()

def add_scene_event(
    scene_id: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Add an event to a scene using the new models."""
    session = Session()
    try:
        # Get the scene
        scene = session.query(Scene).filter_by(id=scene_id).first()
        if not scene:
            return False
        
        # Get the game
        game = scene.game
        
        # Add the event
        game.add_scene_event(
            scene_id=scene_id,
            description=description,
            metadata=metadata or {}
        )
        
        # Commit the changes
        session.commit()
        return True
    finally:
        session.close()

# Poll functions
# (Similar adapter functions for polls) 