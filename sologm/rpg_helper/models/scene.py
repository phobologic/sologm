"""
Scene model for the RPG Helper application.
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum as SQLAEnum, Integer
from sqlalchemy.orm import relationship, object_session

from sologm.rpg_helper.utils.logging import get_logger
from .base import BaseModel, get_session, close_session, NotFoundError
from .scene_event import SceneEvent
from .game.errors import SceneNotFoundError, InvalidSceneStateError, SceneStateTransitionError

if TYPE_CHECKING:
    from .game.base import Game

logger = get_logger()

class SceneStatus(str, Enum):
    """Status of a scene."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class Scene(BaseModel):
    """
    SQLAlchemy model for scenes.
    
    Represents a scene in a game, which can contain multiple events.
    """
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLAEnum(SceneStatus), nullable=False, default=SceneStatus.ACTIVE)
    completed_at = Column(DateTime, nullable=True)
    order = Column(Integer, nullable=False, default=0)
    
    # Foreign key to game
    game_id = Column(String(36), ForeignKey('games.id'), nullable=False, index=True)
    
    # Relationships
    game = relationship("Game", foreign_keys=[game_id], back_populates="scenes")
    events = relationship("SceneEvent", back_populates="scene", cascade="all, delete-orphan", 
                         order_by="SceneEvent.created_at")
    
    def __init__(self, **kwargs):
        """Initialize a new scene."""
        # Set default status if not provided
        if 'status' not in kwargs:
            kwargs['status'] = SceneStatus.ACTIVE
        
        # If order is not specified, set it to the next available order
        if 'order' not in kwargs and 'game_id' in kwargs:
            kwargs['order'] = self._get_next_order(kwargs['game_id'])
            
        super().__init__(**kwargs)
        logger.info(
            "Created new scene",
            scene_id=self.id,
            game_id=self.game_id,
            title=self.title,
            status=self.status.value,
            order=self.order
        )
    
    def __repr__(self):
        """String representation of the scene."""
        return f"<Scene(id='{self.id}', game_id='{self.game_id}', title='{self.title}', status='{self.status.value}', order={self.order})>"
    
    @classmethod
    def _get_next_order(cls, game_id: str) -> int:
        """
        Get the next available order for a scene in a game.
        
        Args:
            game_id: ID of the game
            
        Returns:
            Next available order
        """
        session = get_session()
        try:
            # Get the maximum order value for scenes in this game
            max_order = session.query(cls).filter_by(game_id=game_id).with_entities(
                cls.order
            ).order_by(cls.order.desc()).first()
            
            # If there are no scenes yet, start with 0
            if max_order is None:
                return 0
                
            # Otherwise, use the next order
            return max_order[0] + 1
        finally:
            close_session(session)
    
    def reorder(self, new_order: int) -> None:
        """
        Change the order of this scene.
        
        Args:
            new_order: New order value
            
        Note:
            This method does not handle reordering other scenes.
            Use the reorder_scenes class method for that.
        """
        old_order = self.order
        self.order = new_order
        self.updated_at = datetime.now()
        
        logger.debug(
            "Reordered scene",
            scene_id=self.id,
            old_order=old_order,
            new_order=new_order
        )
        
        # Save changes if the scene is already in a session
        session = object_session(self)
        if session:
            session.commit()
    
    @classmethod
    def reorder_scenes(cls, game_id: str, scene_orders: Dict[str, int]) -> None:
        """
        Reorder multiple scenes in a game.
        
        Args:
            game_id: ID of the game
            scene_orders: Dictionary mapping scene IDs to new order values
        """
        session = get_session()
        try:
            # Get all scenes for this game
            scenes = session.query(cls).filter_by(game_id=game_id).all()
            
            # Update orders
            for scene in scenes:
                if scene.id in scene_orders:
                    scene.order = scene_orders[scene.id]
                    scene.updated_at = datetime.now()
            
            session.commit()
            
            logger.info(
                "Reordered scenes in game",
                game_id=game_id,
                scene_count=len(scene_orders)
            )
        finally:
            close_session(session)
    
    def add_event(self, description: str) -> SceneEvent:
        """
        Add an event to the scene.
        
        Args:
            description: Description of the event
            
        Returns:
            The created event
            
        Raises:
            InvalidSceneStateError: If the scene is not active
        """
        if self.status != SceneStatus.ACTIVE:
            logger.warning(
                "Attempted to add event to non-active scene",
                scene_id=self.id,
                status=self.status.value
            )
            raise InvalidSceneStateError(
                self.id, self.status.value, SceneStatus.ACTIVE.value
            )
        
        event = SceneEvent(
            description=description,
            scene_id=self.id
        )
        
        self.events.append(event)
        self.updated_at = datetime.now()
        
        # Save the event if the scene is already in a session
        session = object_session(self)
        if session:
            session.add(event)
            session.commit()
        
        logger.debug(
            "Added event to scene",
            scene_id=self.id,
            event_id=event.id
        )
        
        return event
    
    def complete(self) -> None:
        """
        Mark the scene as completed.
        
        Raises:
            SceneStateTransitionError: If the scene is not in an active state
        """
        if self.status != SceneStatus.ACTIVE:
            logger.warning(
                "Attempted to complete non-active scene",
                scene_id=self.id,
                status=self.status.value
            )
            raise SceneStateTransitionError(
                self.id, self.status.value, SceneStatus.COMPLETED.value
            )
        
        self.status = SceneStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
        
        logger.info(
            "Completed scene",
            scene_id=self.id,
            game_id=self.game_id
        )
        
        # Save changes if the scene is already in a session
        session = object_session(self)
        if session:
            session.commit()
    
    def abandon(self) -> None:
        """
        Mark the scene as abandoned.
        
        Raises:
            SceneStateTransitionError: If the scene is not in an active state
        """
        if self.status != SceneStatus.ACTIVE:
            logger.warning(
                "Attempted to abandon non-active scene",
                scene_id=self.id,
                status=self.status.value
            )
            raise SceneStateTransitionError(
                self.id, self.status.value, SceneStatus.ABANDONED.value
            )
        
        self.status = SceneStatus.ABANDONED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
        
        logger.info(
            "Abandoned scene",
            scene_id=self.id,
            game_id=self.game_id
        )
        
        # Save changes if the scene is already in a session
        session = object_session(self)
        if session:
            session.commit()
    
    def is_active(self) -> bool:
        """Check if the scene is active."""
        return self.status == SceneStatus.ACTIVE
    
    def is_completed(self) -> bool:
        """Check if the scene is completed."""
        return self.status == SceneStatus.COMPLETED
    
    def is_abandoned(self) -> bool:
        """Check if the scene is abandoned."""
        return self.status == SceneStatus.ABANDONED
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        
        # Convert status enum to string
        data['status'] = self.status.value
        
        # Add events
        data['events'] = [event.to_dict() for event in self.events]
        
        return data
    
    @classmethod
    def get_by_game(cls, game_id: str, status: Optional[SceneStatus] = None) -> List[Scene]:
        """
        Get scenes for a game, optionally filtered by status.
        
        Args:
            game_id: ID of the game
            status: Optional status to filter by
            
        Returns:
            List of scenes ordered by their order field
        """
        session = get_session()
        try:
            query = session.query(cls).filter_by(game_id=game_id)
            
            if status:
                query = query.filter_by(status=status)
            
            # Order by the order field
            query = query.order_by(cls.order)
            
            scenes = query.all()
            
            logger.debug(
                "Retrieved scenes for game",
                game_id=game_id,
                status=status.value if status else "all",
                count=len(scenes)
            )
            
            return scenes
        finally:
            close_session(session)
    
    @classmethod
    def get_for_game(cls, game_id: str, scene_id: str) -> Scene:
        """
        Get a scene for a game by ID.
        
        Args:
            game_id: ID of the game
            scene_id: ID of the scene
            
        Returns:
            The scene
            
        Raises:
            SceneNotFoundError: If the scene is not found
        """
        session = get_session()
        try:
            scene = session.query(cls).filter_by(game_id=game_id, id=scene_id).first()
            
            if not scene:
                logger.warning(
                    "Scene not found for game",
                    game_id=game_id,
                    scene_id=scene_id
                )
                raise SceneNotFoundError(scene_id, game_id)
            
            logger.debug(
                "Retrieved scene for game",
                game_id=game_id,
                scene_id=scene_id
            )
            
            return scene
        finally:
            close_session(session) 