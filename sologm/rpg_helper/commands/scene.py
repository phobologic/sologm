"""
Scene commands for the RPG Helper bot.
"""
from typing import Optional, List, Dict, Any

from sologm.rpg_helper.models import (
    Game, Scene, SceneStatus,
    SceneError, SceneNotFoundError, InvalidSceneStatusError
)
from sologm.rpg_helper.models.init_db import init_db
from sologm.rpg_helper.utils.logging import get_logger

# Initialize the database at module load time
init_db()

logger = get_logger()

def create_scene_command(
    game_id: str,
    title: str,
    description: str = ""
) -> Dict[str, Any]:
    """
    Create a new scene.
    
    Args:
        game_id: The game ID
        title: The title of the scene
        description: The description of the scene
        
    Returns:
        The created scene as a dictionary
        
    Raises:
        NotFoundError: If the game is not found
    """
    logger.info(
        "Creating scene",
        game_id=game_id,
        title=title
    )
    
    session = init_db()[1]()
    try:
        # Get the game
        game = session.query(Game).filter_by(id=game_id).first()
        if not game:
            raise Game.NotFoundError(f"Game with ID {game_id} not found")
        
        # Create the scene
        scene = game.create_scene(
            title=title,
            description=description
        )
        
        # Commit the changes
        session.commit()
        
        logger.info(
            "Scene created",
            game_id=game_id,
            scene_id=scene.id,
            title=scene.title
        )
        
        return scene.to_dict()
    finally:
        session.close()

def get_scene_command(scene_id: str) -> Dict[str, Any]:
    """
    Get a scene.
    
    Args:
        scene_id: The scene ID
        
    Returns:
        The scene as a dictionary
        
    Raises:
        NotFoundError: If the scene is not found
    """
    session = init_db()[1]()
    try:
        # Get the scene
        scene = session.query(Scene).filter_by(id=scene_id).first()
        if not scene:
            raise SceneNotFoundError(f"Scene with ID {scene_id} not found")
        
        return scene.to_dict()
    finally:
        session.close()

def get_scenes_command(game_id: str) -> List[Dict[str, Any]]:
    """
    Get all scenes for a game.
    
    Args:
        game_id: The game ID
        
    Returns:
        List of scenes as dictionaries
        
    Raises:
        NotFoundError: If the game is not found
    """
    session = init_db()[1]()
    try:
        # Get the game
        game = session.query(Game).filter_by(id=game_id).first()
        if not game:
            raise Game.NotFoundError(f"Game with ID {game_id} not found")
        
        # Get the scenes
        scenes = game.get_scenes()
        
        return [scene.to_dict() for scene in scenes]
    finally:
        session.close()

def update_scene_status_command(
    scene_id: str,
    status: str
) -> Dict[str, Any]:
    """
    Update the status of a scene.
    
    Args:
        scene_id: The scene ID
        status: The new status
        
    Returns:
        The updated scene as a dictionary
        
    Raises:
        NotFoundError: If the scene is not found
        InvalidSceneStatusError: If the status is invalid
    """
    logger.info(
        "Updating scene status",
        scene_id=scene_id,
        status=status
    )
    
    session = init_db()[1]()
    try:
        # Get the scene
        scene = session.query(Scene).filter_by(id=scene_id).first()
        if not scene:
            raise SceneNotFoundError(f"Scene with ID {scene_id} not found")
        
        # Update the status
        try:
            scene.status = SceneStatus(status)
        except ValueError:
            valid_statuses = [s.value for s in SceneStatus]
            raise InvalidSceneStatusError(
                f"Invalid status: {status}. Valid statuses are: {', '.join(valid_statuses)}"
            )
        
        # Commit the changes
        session.commit()
        
        logger.info(
            "Scene status updated",
            scene_id=scene_id,
            status=status
        )
        
        return scene.to_dict()
    finally:
        session.close()

def add_scene_event_command(
    scene_id: str,
    description: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Add an event to a scene.
    
    Args:
        scene_id: The scene ID
        description: The description of the event
        metadata: Additional metadata for the event
        
    Returns:
        The created event as a dictionary
        
    Raises:
        NotFoundError: If the scene is not found
    """
    logger.info(
        "Adding scene event",
        scene_id=scene_id,
        description=description
    )
    
    session = init_db()[1]()
    try:
        # Get the scene
        scene = session.query(Scene).filter_by(id=scene_id).first()
        if not scene:
            raise SceneNotFoundError(f"Scene with ID {scene_id} not found")
        
        # Get the game
        game = scene.game
        
        # Add the event
        event = game.add_scene_event(
            scene_id=scene_id,
            description=description,
            metadata=metadata or {}
        )
        
        # Commit the changes
        session.commit()
        
        logger.info(
            "Scene event added",
            scene_id=scene_id,
            event_id=event.id
        )
        
        return event.to_dict()
    finally:
        session.close()

def get_scene_events_command(scene_id: str) -> List[Dict[str, Any]]:
    """
    Get all events for a scene.
    
    Args:
        scene_id: The scene ID
        
    Returns:
        List of events as dictionaries
        
    Raises:
        NotFoundError: If the scene is not found
    """
    session = init_db()[1]()
    try:
        # Get the scene
        scene = session.query(Scene).filter_by(id=scene_id).first()
        if not scene:
            raise SceneNotFoundError(f"Scene with ID {scene_id} not found")
        
        # Get the events
        events = scene.events
        
        return [event.to_dict() for event in events]
    finally:
        session.close()

# Additional helper functions as needed 