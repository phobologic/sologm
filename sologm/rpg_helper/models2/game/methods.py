"""
Additional methods for the Game model.
"""
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

from sqlalchemy.orm import object_session

from sologm.rpg_helper.utils.logging import get_logger
from sologm.rpg_helper.models2.base import get_session, close_session
from sologm.rpg_helper.models2.game.base import Game
from sologm.rpg_helper.models2.game.errors import SceneNotFoundError, PollNotFoundError

if TYPE_CHECKING:
    from sologm.rpg_helper.models2.scene import Scene, SceneStatus
    from sologm.rpg_helper.models2.poll import Poll, PollStatus
    from sologm.rpg_helper.models2.scene_event import SceneEvent

logger = get_logger()

# Add scene management methods to Game
def create_scene(self, title: str, description: Optional[str] = None) -> 'Scene':
    """
    Create a new scene in the game.
    
    Args:
        title: The scene title
        description: Optional scene description
        
    Returns:
        The created scene
    """
    from sologm.rpg_helper.models2.scene import Scene
    
    scene = Scene(
        title=title,
        description=description,
        game_id=self.id
    )
    
    self.scenes.append(scene)
    self.updated_at = datetime.now()
    
    # Save the scene if the game is already in a session
    session = object_session(self)
    if session:
        session.add(scene)
        session.commit()
    
    logger.info(
        "Created new scene in game",
        game_id=self.id,
        scene_id=scene.id,
        title=title
    )
    
    return scene

def get_scene(self, scene_id: str) -> 'Scene':
    """
    Get a scene by ID.
    
    Args:
        scene_id: The scene ID
        
    Returns:
        The scene
        
    Raises:
        SceneNotFoundError: If the scene is not found
    """
    from sologm.rpg_helper.models2.scene import Scene
    
    for scene in self.scenes:
        if scene.id == scene_id:
            logger.debug(
                "Retrieved scene from game",
                game_id=self.id,
                scene_id=scene_id
            )
            return scene
    
    # If not found in loaded scenes, try to load it from the database
    return Scene.get_for_game(self.id, scene_id)

def get_scenes(self, status: Optional['SceneStatus'] = None) -> List['Scene']:
    """
    Get all scenes in the game, optionally filtered by status.
    
    Args:
        status: Optional status to filter by
        
    Returns:
        List of scenes
    """
    from sologm.rpg_helper.models2.scene import Scene
    
    # If scenes are already loaded and no status filter, return them
    if 'scenes' in self.__dict__ and status is None:
        logger.debug(
            "Retrieved all scenes from game (cached)",
            game_id=self.id,
            count=len(self.scenes)
        )
        return self.scenes
    
    # Otherwise, query the database
    return Scene.get_by_game(self.id, status)

def add_scene_event(self, scene_id: str, description: str) -> 'SceneEvent':
    """
    Add an event to a scene.
    
    Args:
        scene_id: The scene ID
        description: The event description
        
    Returns:
        The created event
        
    Raises:
        SceneNotFoundError: If the scene is not found
    """
    scene = self.get_scene(scene_id)
    event = scene.add_event(description)
    
    logger.info(
        "Added event to scene in game",
        game_id=self.id,
        scene_id=scene_id,
        event_id=event.id
    )
    
    return event

def complete_scene(self, scene_id: str) -> None:
    """
    Mark a scene as completed.
    
    Args:
        scene_id: The scene ID
        
    Raises:
        SceneNotFoundError: If the scene is not found
    """
    scene = self.get_scene(scene_id)
    scene.complete()
    
    logger.info(
        "Completed scene in game",
        game_id=self.id,
        scene_id=scene_id
    )

def abandon_scene(self, scene_id: str) -> None:
    """
    Mark a scene as abandoned.
    
    Args:
        scene_id: The scene ID
        
    Raises:
        SceneNotFoundError: If the scene is not found
    """
    scene = self.get_scene(scene_id)
    scene.abandon()
    
    logger.info(
        "Abandoned scene in game",
        game_id=self.id,
        scene_id=scene_id
    )

def reorder_scenes(self, scene_orders: Dict[str, int]) -> None:
    """
    Reorder scenes in the game.
    
    Args:
        scene_orders: Dictionary mapping scene IDs to new order values
    """
    from sologm.rpg_helper.models2.scene import Scene
    
    # Update orders in memory
    for scene in self.scenes:
        if scene.id in scene_orders:
            scene.order = scene_orders[scene.id]
            scene.updated_at = datetime.now()
    
    # Save changes if the game is already in a session
    session = object_session(self)
    if session:
        session.commit()
    else:
        # Otherwise, use the class method
        Scene.reorder_scenes(self.id, scene_orders)
    
    logger.info(
        "Reordered scenes in game",
        game_id=self.id,
        scene_count=len(scene_orders)
    )

# Add poll management methods to Game
def create_poll(self, question: str, options: List[str], timeout: Optional[int] = None) -> 'Poll':
    """
    Create a new poll in the game.
    
    Args:
        question: The poll question
        options: List of poll options
        timeout: Optional timeout in seconds
        
    Returns:
        The created poll
    """
    from sologm.rpg_helper.models2.poll import Poll
    
    poll = Poll(
        question=question,
        options=options,
        game_id=self.id,
        timeout=timeout
    )
    
    self.polls.append(poll)
    self.updated_at = datetime.now()
    
    # Save the poll if the game is already in a session
    session = object_session(self)
    if session:
        session.add(poll)
        session.commit()
    
    logger.info(
        "Created new poll in game",
        game_id=self.id,
        poll_id=poll.id,
        question=question,
        option_count=len(options),
        timeout=timeout
    )
    
    return poll

def get_poll(self, poll_id: str) -> 'Poll':
    """
    Get a poll by ID.
    
    Args:
        poll_id: The poll ID
        
    Returns:
        The poll
        
    Raises:
        PollNotFoundError: If the poll is not found
    """
    from sologm.rpg_helper.models2.poll import Poll
    
    for poll in self.polls:
        if poll.id == poll_id:
            logger.debug(
                "Retrieved poll from game",
                game_id=self.id,
                poll_id=poll_id
            )
            return poll
    
    # If not found in loaded polls, try to load it from the database
    return Poll.get_for_game(self.id, poll_id)

def get_polls(self, status: Optional['PollStatus'] = None) -> List['Poll']:
    """
    Get all polls in the game, optionally filtered by status.
    
    Args:
        status: Optional status to filter by
        
    Returns:
        List of polls
    """
    from sologm.rpg_helper.models2.poll import Poll
    
    # If polls are already loaded and no status filter, return them
    if 'polls' in self.__dict__ and status is None:
        logger.debug(
            "Retrieved all polls from game (cached)",
            game_id=self.id,
            count=len(self.polls)
        )
        return self.polls
    
    # Otherwise, query the database
    return Poll.get_by_game(self.id, status)

def close_poll(self, poll_id: str) -> None:
    """
    Close a poll.
    
    Args:
        poll_id: The poll ID
        
    Raises:
        PollNotFoundError: If the poll is not found
    """
    poll = self.get_poll(poll_id)
    poll.close()
    
    logger.info(
        "Closed poll in game",
        game_id=self.id,
        poll_id=poll_id
    )

def add_vote(self, poll_id: str, user_id: str, option_index: int) -> None:
    """
    Add a vote to a poll.
    
    Args:
        poll_id: The poll ID
        user_id: The user ID
        option_index: The option index
        
    Raises:
        PollNotFoundError: If the poll is not found
        PollClosedError: If the poll is closed
        ValueError: If the option index is invalid
    """
    poll = self.get_poll(poll_id)
    poll.add_vote(user_id, option_index)
    
    logger.info(
        "Added vote to poll in game",
        game_id=self.id,
        poll_id=poll_id,
        user_id=user_id,
        option_index=option_index
    )

# Add the methods to the Game class
Game.create_scene = create_scene
Game.get_scene = get_scene
Game.get_scenes = get_scenes
Game.add_scene_event = add_scene_event
Game.complete_scene = complete_scene
Game.abandon_scene = abandon_scene
Game.reorder_scenes = reorder_scenes

Game.create_poll = create_poll
Game.get_poll = get_poll
Game.get_polls = get_polls
Game.close_poll = close_poll
Game.add_vote = add_vote 