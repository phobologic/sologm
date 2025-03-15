"""
Game service for managing game operations.
"""
from typing import List, Dict, Any, Optional, Union, TYPE_CHECKING
from datetime import datetime

from sqlalchemy.orm import object_session

from sologm.rpg_helper.models.game.base import Game
from sologm.rpg_helper.models.scene import Scene, SceneStatus
from sologm.rpg_helper.models.scene_event import SceneEvent
from sologm.rpg_helper.models.poll import Poll, PollStatus
from sologm.rpg_helper.models.game.errors import (
    SceneNotFoundError, InvalidSceneStateError, SceneStateTransitionError,
    PollNotFoundError, PollClosedError
)
from sologm.rpg_helper.db.config import get_session, close_session
from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger()

class GameService:
    """Service for managing game operations."""
    
    def __init__(self, game: Game):
        """Initialize with a game instance."""
        self.game = game
    
    @classmethod
    def for_game_id(cls, game_id: str) -> 'GameService':
        """Create a service for a game by ID."""
        session = get_session()
        try:
            game = session.query(Game).filter_by(id=game_id).first()
            if not game:
                raise ValueError(f"Game with ID {game_id} not found")
            return cls(game)
        finally:
            close_session(session)
    
    def get_scene(self, scene_id: str) -> Scene:
        """
        Get a scene by ID.
        
        Args:
            scene_id: The scene ID
            
        Returns:
            The scene
            
        Raises:
            SceneNotFoundError: If the scene is not found or doesn't belong to this game
        """
        # First try to get from game's scenes collection
        for scene in self.game.scenes:
            if scene.id == scene_id:
                return scene
        
        # If not found in collection, query the database
        session = object_session(self.game)
        if session:
            scene = session.query(Scene).filter_by(
                id=scene_id,
                game_id=self.game.id
            ).first()
            if scene:
                return scene
        
        logger.warning(
            "Scene not found",
            scene_id=scene_id,
            game_id=self.game.id
        )
        raise SceneNotFoundError(scene_id, self.game.id)
    
    def get_poll(self, poll_id: str) -> Poll:
        """
        Get a poll by ID.
        
        Args:
            poll_id: The poll ID
            
        Returns:
            The poll
            
        Raises:
            PollNotFoundError: If the poll is not found or doesn't belong to this game
        """
        # First try to get from game's polls collection
        for poll in self.game.polls:
            if poll.id == poll_id:
                return poll
        
        # If not found in collection, query the database
        session = object_session(self.game)
        if session:
            poll = session.query(Poll).filter_by(
                id=poll_id,
                game_id=self.game.id
            ).first()
            if poll:
                return poll
        
        logger.warning(
            "Poll not found",
            poll_id=poll_id,
            game_id=self.game.id
        )
        raise PollNotFoundError(poll_id, self.game.id)
    
    def create_scene(self, title: str, description: Optional[str] = None) -> Scene:
        """
        Create a new scene in the game.
        
        Args:
            title: The scene title
            description: Optional scene description
            
        Returns:
            The created scene
        """
        scene = Scene(
            title=title,
            description=description,
            game_id=self.game.id
        )
        
        self.game.scenes.append(scene)
        self.game.updated_at = datetime.now()
        
        # Save changes
        session = object_session(self.game)
        if session:
            session.add(scene)
            session.commit()
        
        logger.info(
            "Created new scene in game",
            game_id=self.game.id,
            scene_id=scene.id,
            title=title
        )
        
        return scene
    
    def create_poll(self, question: str, options: List[str]) -> Poll:
        """
        Create a new poll in the game.
        
        Args:
            question: The poll question
            options: List of poll options
            
        Returns:
            The created poll
        """
        poll = Poll(
            question=question,
            options=options,
            game_id=self.game.id
        )
        
        self.game.polls.append(poll)
        self.game.updated_at = datetime.now()
        
        # Save the poll if the game is already in a session
        session = object_session(self.game)
        if session:
            session.add(poll)
            session.commit()
        
        logger.info(
            "Created new poll in game",
            game_id=self.game.id,
            poll_id=poll.id,
            question=question
        )
        
        return poll