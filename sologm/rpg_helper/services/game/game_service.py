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
    
    # Scene operations
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
    
    def get_scene(self, scene_id: str) -> Scene:
        """
        Get a scene by ID.
        
        Args:
            scene_id: The scene ID
            
        Returns:
            The scene
            
        Raises:
            SceneNotFoundError: If the scene is not found
        """
        # First try to get the scene from the scenes relationship
        for scene in self.game.scenes:
            if scene.id == scene_id:
                return scene
        
        # If not found, query the database
        session = object_session(self.game)
        if session:
            scene = session.query(Scene).filter_by(id=scene_id, game_id=self.game.id).first()
            if scene:
                return scene
        
        # If still not found, raise an error
        raise SceneNotFoundError(scene_id, self.game.id)
    
    def get_scenes(self, status: Optional[str] = None) -> List[Scene]:
        """
        Get all scenes in the game, optionally filtered by status.
        
        Args:
            status: Optional status to filter by
            
        Returns:
            List of scenes
        """
        # Get all scenes
        scenes = list(self.game.scenes)
        
        # Filter by status if provided
        if status:
            try:
                status_enum = SceneStatus(status)
                scenes = [scene for scene in scenes if scene.status == status_enum]
            except ValueError:
                logger.warning(
                    "Invalid scene status",
                    status=status
                )
                return []
        
        # Sort by order
        scenes.sort(key=lambda s: s.order)
        
        return scenes
    
    def add_scene_event(self, scene_id: str, description: str, metadata: Optional[Dict[str, Any]] = None) -> SceneEvent:
        """
        Add an event to a scene.
        
        Args:
            scene_id: The scene ID
            description: The event description
            metadata: Optional metadata for the event
            
        Returns:
            The created event
            
        Raises:
            SceneNotFoundError: If the scene is not found
        """
        # Get the scene
        scene = self.get_scene(scene_id)
        
        # Create the event
        event = SceneEvent(
            scene_id=scene_id,
            description=description,
            metadata=metadata or {}
        )
        
        # Add the event to the scene
        scene.events.append(event)
        scene.updated_at = datetime.now()
        self.game.updated_at = datetime.now()
        
        # Save the event if the game is already in a session
        session = object_session(self.game)
        if session:
            session.add(event)
            session.commit()
        
        logger.info(
            "Added event to scene in game",
            game_id=self.game.id,
            scene_id=scene_id,
            event_id=event.id
        )
        
        return event
    
    def complete_scene(self, scene_id: str) -> Scene:
        """
        Mark a scene as completed.
        
        Args:
            scene_id: The scene ID
            
        Returns:
            The updated scene
            
        Raises:
            SceneNotFoundError: If the scene is not found
            SceneStateTransitionError: If the scene cannot transition to completed state
        """
        # Get the scene
        scene = self.get_scene(scene_id)
        
        # Check if the scene can be completed
        if scene.status != SceneStatus.ACTIVE:
            raise SceneStateTransitionError(
                scene_id=scene_id,
                current_state=scene.status.value,
                requested_state=SceneStatus.COMPLETED.value
            )
        
        # Update the scene
        scene.status = SceneStatus.COMPLETED
        scene.updated_at = datetime.now()
        self.game.updated_at = datetime.now()
        
        # Save the changes if the game is already in a session
        session = object_session(self.game)
        if session:
            session.commit()
        
        logger.info(
            "Completed scene in game",
            game_id=self.game.id,
            scene_id=scene_id
        )
        
        return scene
    
    def abandon_scene(self, scene_id: str) -> Scene:
        """
        Mark a scene as abandoned.
        
        Args:
            scene_id: The scene ID
            
        Returns:
            The updated scene
            
        Raises:
            SceneNotFoundError: If the scene is not found
            SceneStateTransitionError: If the scene cannot transition to abandoned state
        """
        # Get the scene
        scene = self.get_scene(scene_id)
        
        # Check if the scene can be abandoned
        if scene.status != SceneStatus.ACTIVE:
            raise SceneStateTransitionError(
                scene_id=scene_id,
                current_state=scene.status.value,
                requested_state=SceneStatus.ABANDONED.value
            )
        
        # Update the scene
        scene.status = SceneStatus.ABANDONED
        scene.updated_at = datetime.now()
        self.game.updated_at = datetime.now()
        
        # Save the changes if the game is already in a session
        session = object_session(self.game)
        if session:
            session.commit()
        
        logger.info(
            "Abandoned scene in game",
            game_id=self.game.id,
            scene_id=scene_id
        )
        
        return scene
    
    def reorder_scenes(self, scene_ids: List[str]) -> List[Scene]:
        """
        Reorder scenes.
        
        Args:
            scene_ids: List of scene IDs in the desired order
            
        Returns:
            List of updated scenes
            
        Raises:
            SceneNotFoundError: If a scene is not found
        """
        # Get all scenes
        scenes = {scene.id: scene for scene in self.game.scenes}
        
        # Check if all scene IDs are valid
        for scene_id in scene_ids:
            if scene_id not in scenes:
                raise SceneNotFoundError(scene_id, self.game.id)
        
        # Update the order
        for i, scene_id in enumerate(scene_ids):
            scenes[scene_id].order = i
            scenes[scene_id].updated_at = datetime.now()
        
        self.game.updated_at = datetime.now()
        
        # Save the changes if the game is already in a session
        session = object_session(self.game)
        if session:
            session.commit()
        
        logger.info(
            "Reordered scenes in game",
            game_id=self.game.id,
            scene_count=len(scene_ids)
        )
        
        # Return the scenes in the new order
        return [scenes[scene_id] for scene_id in scene_ids]
    
    # Poll operations
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
    
    def get_poll(self, poll_id: str) -> Poll:
        """
        Get a poll by ID.
        
        Args:
            poll_id: The poll ID
            
        Returns:
            The poll
            
        Raises:
            PollNotFoundError: If the poll is not found
        """
        # First try to get the poll from the polls relationship
        for poll in self.game.polls:
            if poll.id == poll_id:
                return poll
        
        # If not found, query the database
        session = object_session(self.game)
        if session:
            poll = session.query(Poll).filter_by(id=poll_id, game_id=self.game.id).first()
            if poll:
                return poll
        
        # If still not found, raise an error
        raise PollNotFoundError(poll_id, self.game.id)
    
    def get_polls(self, status: Optional[str] = None) -> List[Poll]:
        """
        Get all polls in the game, optionally filtered by status.
        
        Args:
            status: Optional status to filter by
            
        Returns:
            List of polls
        """
        # Get all polls
        polls = list(self.game.polls)
        
        # Filter by status if provided
        if status:
            try:
                status_enum = PollStatus(status)
                polls = [poll for poll in polls if poll.status == status_enum]
            except ValueError:
                logger.warning(
                    "Invalid poll status",
                    status=status
                )
                return []
        
        # Sort by creation date
        polls.sort(key=lambda p: p.created_at)
        
        return polls
    
    def close_poll(self, poll_id: str) -> Poll:
        """
        Close a poll.
        
        Args:
            poll_id: The poll ID
            
        Returns:
            The updated poll
            
        Raises:
            PollNotFoundError: If the poll is not found
        """
        # Get the poll
        poll = self.get_poll(poll_id)
        
        # Close the poll
        poll.close()
        self.game.updated_at = datetime.now()
        
        # Save the changes if the game is already in a session
        session = object_session(self.game)
        if session:
            session.commit()
        
        logger.info(
            "Closed poll in game",
            game_id=self.game.id,
            poll_id=poll_id
        )
        
        return poll
    
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
        # Get the poll
        poll = self.get_poll(poll_id)
        
        # Add the vote
        poll.add_vote(user_id, option_index)
        self.game.updated_at = datetime.now()
        
        # Save the changes if the game is already in a session
        session = object_session(self.game)
        if session:
            session.commit()
        
        logger.info(
            "Added vote to poll in game",
            game_id=self.game.id,
            poll_id=poll_id,
            user_id=user_id,
            option_index=option_index
        ) 