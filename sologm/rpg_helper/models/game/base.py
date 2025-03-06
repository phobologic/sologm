"""
Base game model.
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Set, TYPE_CHECKING, Type, ClassVar

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Table, Boolean, Enum as SQLAlchemyEnum, UniqueConstraint
from sqlalchemy.orm import relationship, object_session

from sologm.rpg_helper.utils.logging import get_logger
from sologm.rpg_helper.models.base import BaseModel, get_session, close_session, NotFoundError
from sologm.rpg_helper.models.game.errors import (
    GameError, ChannelGameExistsError, SceneNotFoundError, PollNotFoundError
)
from sologm.rpg_helper.models.user import user_game_association

if TYPE_CHECKING:
    from sologm.rpg_helper.models.scene import Scene, SceneStatus
    from sologm.rpg_helper.models.poll import Poll, PollStatus
    from sologm.rpg_helper.models.user import User

logger = get_logger()

# Association table for game-user many-to-many relationship
game_users = Table(
    'game_users',
    BaseModel.metadata,
    Column('game_id', String(36), ForeignKey('games.id'), primary_key=True),
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True)
)

class GameType(Enum):
    """Game type enumeration."""
    STANDARD = "standard"
    MYTHIC = "mythic"
    # Add more game types as needed


class Game(BaseModel):
    """
    SQLAlchemy model for games.
    
    Represents a game, which can have multiple scenes, polls, and members.
    """
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    channel_id = Column(String(36), nullable=False)
    workspace_id = Column(String(36), nullable=False)
    game_type = Column(SQLAlchemyEnum(GameType), nullable=False, default=GameType.STANDARD)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    members = relationship("User", secondary=user_game_association, back_populates="games")
    scenes = relationship("Scene", back_populates="game", cascade="all, delete-orphan")
    polls = relationship("Poll", back_populates="game", cascade="all, delete-orphan")
    settings = relationship("GameSetting", back_populates="game", cascade="all, delete-orphan")
    
    # Table constraints
    __table_args__ = (
        # Ensure channel_id and workspace_id are unique together
        UniqueConstraint('channel_id', 'workspace_id', name='uix_game_channel_workspace'),
    )
    
    # Polymorphic identity for inheritance
    __mapper_args__ = {
        'polymorphic_on': game_type,
        'polymorphic_identity': GameType.STANDARD
    }
    
    # Class variables for type-specific game classes
    _game_types: ClassVar[Dict[str, Type[Game]]] = {}
    
    def __init__(self, **kwargs):
        """Initialize a new game."""
        super().__init__(**kwargs)
        logger.info(
            "Created new game",
            id=self.id,
            name=self.name,
            type=self.game_type
        )
    
    def __repr__(self):
        """Return a string representation of the game."""
        return f"<Game(id='{self.id}', name='{self.name}', type='{self.game_type}')>"
    
    @classmethod
    def register_game_type(cls, game_type: str, game_class: Type[Game]) -> None:
        """
        Register a game type with its corresponding class.
        
        Args:
            game_type: The game type string
            game_class: The game class
        """
        cls._game_types[game_type] = game_class
        logger.debug(
            "Registered game type",
            game_type=game_type,
            game_class=game_class.__name__
        )
    
    @classmethod
    def create(cls, **kwargs) -> Game:
        """
        Create a new game of the appropriate type.
        
        Args:
            **kwargs: Game attributes
            
        Returns:
            The created game
            
        Raises:
            ChannelGameExistsError: If a game already exists in the channel
        """
        # Check if a game already exists in the channel
        channel_id = kwargs.get('channel_id')
        if channel_id:
            existing_game = cls.get_by_channel(channel_id)
            if existing_game:
                logger.warning(
                    "Attempted to create game in channel with existing game",
                    channel_id=channel_id,
                    existing_game_id=existing_game.id
                )
                raise ChannelGameExistsError(channel_id, existing_game)
        
        # Determine the game class based on the game type
        game_type = kwargs.get('game_type', GameType.STANDARD.value)
        game_class = cls._game_types.get(game_type, cls)
        
        # Create the game
        game = game_class(**kwargs)
        
        # Save the game
        session = get_session()
        try:
            session.add(game)
            session.commit()
            
            logger.info(
                "Created and saved new game",
                game_id=game.id,
                game_type=game.game_type
            )
            
            return game
        finally:
            close_session(session)
    
    @classmethod
    def get_by_channel(cls, channel_id: str, workspace_id: str) -> Optional['Game']:
        """
        Get a game by channel ID and workspace ID.
        
        Args:
            channel_id: The channel ID
            workspace_id: The workspace ID
            
        Returns:
            The game, or None if not found
        """
        from sologm.rpg_helper.db.config import get_session, close_session
        
        session = get_session()
        try:
            return session.query(cls).filter_by(
                channel_id=channel_id,
                workspace_id=workspace_id
            ).first()
        finally:
            close_session(session)
    
    def add_member(self, user: 'User') -> None:
        """
        Add a user as a member of the game.
        
        Args:
            user: The user to add
        """
        if user not in self.members:
            self.members.append(user)
            self.updated_at = datetime.now()
            
            logger.info(
                "Added member to game",
                game_id=self.id,
                user_id=user.id,
                username=user.username
            )
            
            # Save changes if the game is already in a session
            session = object_session(self)
            if session:
                session.commit()
    
    def remove_member(self, user: 'User') -> None:
        """
        Remove a user from the game.
        
        Args:
            user: The user to remove
        """
        if user in self.members:
            self.members.remove(user)
            self.updated_at = datetime.now()
            
            logger.info(
                "Removed member from game",
                game_id=self.id,
                user_id=user.id,
                username=user.username
            )
            
            # Save changes if the game is already in a session
            session = object_session(self)
            if session:
                session.commit()
    
    def is_member(self, user_id: str) -> bool:
        """
        Check if a user is a member of the game.
        
        Args:
            user_id: The user ID
            
        Returns:
            True if the user is a member, False otherwise
        """
        return any(member.id == user_id for member in self.members)
    
    def get_setting(self, name: str, default: Any = None) -> Any:
        """
        Get a game setting.
        
        Args:
            name: The setting name
            default: Default value if the setting doesn't exist
            
        Returns:
            The setting value, or the default if not found
        """
        from sologm.rpg_helper.models.game.settings import GameSetting
        
        setting = GameSetting.get_for_game(self.id, name)
        
        if setting:
            logger.debug(
                "Retrieved game setting",
                game_id=self.id,
                name=name,
                type=setting.value_type
            )
            return setting.value
        
        logger.debug(
            "Game setting not found, using default",
            game_id=self.id,
            name=name,
            default=default
        )
        
        return default
    
    def set_setting(self, name: str, value: Any) -> None:
        """
        Set a game setting.
        
        Args:
            name: The setting name
            value: The setting value
        """
        from sologm.rpg_helper.models.game.settings import GameSetting
        
        session = object_session(self) or get_session()
        try:
            # Check if the setting already exists
            setting = session.query(GameSetting).filter_by(
                game_id=self.id, name=name
            ).first()
            
            if setting:
                # Update the existing setting
                old_value = setting.value
                setting.value = value
                
                logger.debug(
                    "Updated game setting",
                    game_id=self.id,
                    name=name,
                    old_value=old_value,
                    new_value=value
                )
            else:
                # Create a new setting
                setting = GameSetting(
                    game_id=self.id,
                    name=name
                )
                setting.value = value
                
                session.add(setting)
                
                logger.debug(
                    "Created new game setting",
                    game_id=self.id,
                    name=name,
                    value=value
                )
            
            if session == object_session(self):
                session.commit()
        finally:
            if session != object_session(self):
                close_session(session)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        
        # Add member IDs
        data['member_ids'] = [member.id for member in self.members]
        
        # Add scene IDs
        data['scene_ids'] = [scene.id for scene in self.scenes]
        
        # Add poll IDs
        data['poll_ids'] = [poll.id for poll in self.polls]
        
        # Add settings
        data['settings'] = {
            setting.name: setting.value
            for setting in self.settings
        }
        
        return data
    
    def deactivate(self) -> None:
        """Deactivate the game."""
        if not self.is_active:
            logger.debug(
                "Attempted to deactivate already inactive game",
                game_id=self.id
            )
            return
        
        self.is_active = False
        self.updated_at = datetime.now()
        
        logger.info(
            "Deactivated game",
            game_id=self.id
        )
        
        # Save changes if the game is already in a session
        session = object_session(self)
        if session:
            session.commit()
    
    def activate(self) -> None:
        """Activate the game."""
        if self.is_active:
            logger.debug(
                "Attempted to activate already active game",
                game_id=self.id
            )
            return
        
        self.is_active = True
        self.updated_at = datetime.now()
        
        logger.info(
            "Activated game",
            game_id=self.id
        )
        
        # Save changes if the game is already in a session
        session = object_session(self)
        if session:
            session.commit()

    @classmethod
    def create_for_channel(cls, channel_id: str, workspace_id: str, **kwargs) -> 'Game':
        """
        Create a new game for a channel.
        
        Args:
            channel_id: The channel ID
            workspace_id: The workspace ID
            **kwargs: Additional arguments to pass to the constructor
            
        Returns:
            The created game
            
        Raises:
            ChannelGameExistsError: If a game already exists for the channel
        """
        from sologm.rpg_helper.db.config import get_session, close_session
        
        # Check if a game already exists for this channel
        existing_game = cls.get_by_channel(channel_id, workspace_id)
        if existing_game:
            raise ChannelGameExistsError(channel_id, existing_game)
        
        # Create the game
        kwargs['channel_id'] = channel_id
        kwargs['workspace_id'] = workspace_id
        
        # Determine the game class based on the game type
        game_type = kwargs.get('game_type', GameType.STANDARD.value)
        game_class = cls._game_types.get(game_type, cls)
        
        # Create the game
        game = game_class(**kwargs)
        
        # Save the game
        session = get_session()
        try:
            session.add(game)
            session.commit()
            return game
        finally:
            close_session(session)

    @classmethod
    def get_all_active(cls) -> List['Game']:
        """
        Get all active games.
        
        Returns:
            List of active games
        """
        from sologm.rpg_helper.db.config import get_session, close_session
        
        session = get_session()
        try:
            return session.query(cls).filter_by(is_active=True).all()
        finally:
            close_session(session)

    def create_scene(self, title: str, description: Optional[str] = None) -> 'Scene':
        """
        Create a new scene in the game.
        
        Args:
            title: The scene title
            description: Optional scene description
            
        Returns:
            The created scene
        """
        # Import here to avoid circular imports
        from sologm.rpg_helper.models.scene import Scene
        
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
        # Import here to avoid circular imports
        from sologm.rpg_helper.models.scene import Scene
        
        # First try to get the scene from the scenes relationship
        for scene in self.scenes:
            if scene.id == scene_id:
                return scene
        
        # If not found, query the database
        session = object_session(self)
        if session:
            scene = session.query(Scene).filter_by(id=scene_id, game_id=self.id).first()
            if scene:
                return scene
        
        # If still not found, raise an error
        raise SceneNotFoundError(scene_id, self.id)
    
    def get_scenes(self, status: Optional[str] = None) -> List['Scene']:
        """
        Get all scenes in the game, optionally filtered by status.
        
        Args:
            status: Optional status to filter by
            
        Returns:
            List of scenes
        """
        # Import here to avoid circular imports
        from sologm.rpg_helper.models.scene import Scene, SceneStatus
        
        # Get all scenes
        scenes = list(self.scenes)
        
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

    def add_scene_event(self, scene_id: str, description: str, metadata: Optional[Dict[str, Any]] = None) -> 'SceneEvent':
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
        # Import here to avoid circular imports
        from sologm.rpg_helper.models.scene_event import SceneEvent
        
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
        self.updated_at = datetime.now()
        
        # Save the event if the game is already in a session
        session = object_session(self)
        if session:
            session.add(event)
            session.commit()
        
        logger.info(
            "Added event to scene in game",
            game_id=self.id,
            scene_id=scene_id,
            event_id=event.id
        )
        
        return event 

    def complete_scene(self, scene_id: str) -> 'Scene':
        """
        Mark a scene as completed.
        
        Args:
            scene_id: The scene ID
            
        Returns:
            The updated scene
            
        Raises:
            SceneNotFoundError: If the scene is not found
            InvalidSceneStatusError: If the scene is already completed or abandoned
        """
        # Import here to avoid circular imports
        from sologm.rpg_helper.models.scene import Scene, SceneStatus
        from sologm.rpg_helper.models.game.errors import InvalidSceneStatusError
        
        # Get the scene
        scene = self.get_scene(scene_id)
        
        # Check if the scene can be completed
        if scene.status != SceneStatus.ACTIVE:
            raise InvalidSceneStatusError(
                scene_id=scene_id,
                current_status=scene.status,
                requested_status=SceneStatus.COMPLETED
            )
        
        # Update the scene
        scene.status = SceneStatus.COMPLETED
        scene.updated_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Save the changes if the game is already in a session
        session = object_session(self)
        if session:
            session.commit()
        
        logger.info(
            "Completed scene in game",
            game_id=self.id,
            scene_id=scene_id
        )
        
        return scene

    def abandon_scene(self, scene_id: str) -> 'Scene':
        """
        Mark a scene as abandoned.
        
        Args:
            scene_id: The scene ID
            
        Returns:
            The updated scene
            
        Raises:
            SceneNotFoundError: If the scene is not found
            InvalidSceneStatusError: If the scene is already completed or abandoned
        """
        # Import here to avoid circular imports
        from sologm.rpg_helper.models.scene import Scene, SceneStatus
        from sologm.rpg_helper.models.game.errors import InvalidSceneStatusError
        
        # Get the scene
        scene = self.get_scene(scene_id)
        
        # Check if the scene can be abandoned
        if scene.status != SceneStatus.ACTIVE:
            raise InvalidSceneStatusError(
                scene_id=scene_id,
                current_status=scene.status,
                requested_status=SceneStatus.ABANDONED
            )
        
        # Update the scene
        scene.status = SceneStatus.ABANDONED
        scene.updated_at = datetime.now()
        self.updated_at = datetime.now()
        
        # Save the changes if the game is already in a session
        session = object_session(self)
        if session:
            session.commit()
        
        logger.info(
            "Abandoned scene in game",
            game_id=self.id,
            scene_id=scene_id
        )
        
        return scene

    def reorder_scenes(self, scene_ids: List[str]) -> List['Scene']:
        """
        Reorder scenes.
        
        Args:
            scene_ids: List of scene IDs in the desired order
            
        Returns:
            List of updated scenes
            
        Raises:
            SceneNotFoundError: If a scene is not found
        """
        # Import here to avoid circular imports
        from sologm.rpg_helper.models.scene import Scene
        
        # Get all scenes
        scenes = {scene.id: scene for scene in self.scenes}
        
        # Check if all scene IDs are valid
        for scene_id in scene_ids:
            if scene_id not in scenes:
                raise SceneNotFoundError(scene_id, self.id)
        
        # Update the order
        for i, scene_id in enumerate(scene_ids):
            scenes[scene_id].order = i
            scenes[scene_id].updated_at = datetime.now()
        
        self.updated_at = datetime.now()
        
        # Save the changes if the game is already in a session
        session = object_session(self)
        if session:
            session.commit()
        
        logger.info(
            "Reordered scenes in game",
            game_id=self.id,
            scene_count=len(scene_ids)
        )
        
        # Return the scenes in the new order
        return [scenes[scene_id] for scene_id in scene_ids]

    def create_poll(self, question: str, options: List[str]) -> 'Poll':
        """
        Create a new poll in the game.
        
        Args:
            question: The poll question
            options: List of poll options
            
        Returns:
            The created poll
        """
        # Import here to avoid circular imports
        from sologm.rpg_helper.models.poll import Poll
        
        poll = Poll(
            question=question,
            options=options,
            game_id=self.id
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
            question=question
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
        # Import here to avoid circular imports
        from sologm.rpg_helper.models.poll import Poll
        
        # First try to get the poll from the polls relationship
        for poll in self.polls:
            if poll.id == poll_id:
                return poll
        
        # If not found, query the database
        session = object_session(self)
        if session:
            poll = session.query(Poll).filter_by(id=poll_id, game_id=self.id).first()
            if poll:
                return poll
        
        # If still not found, raise an error
        raise PollNotFoundError(poll_id, self.id)

    def get_polls(self, status: Optional[str] = None) -> List['Poll']:
        """
        Get all polls in the game, optionally filtered by status.
        
        Args:
            status: Optional status to filter by
            
        Returns:
            List of polls
        """
        # Import here to avoid circular imports
        from sologm.rpg_helper.models.poll import Poll, PollStatus
        
        # Get all polls
        polls = list(self.polls)
        
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

    def close_poll(self, poll_id: str) -> 'Poll':
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
        self.updated_at = datetime.now()
        
        # Save the changes if the game is already in a session
        session = object_session(self)
        if session:
            session.commit()
        
        logger.info(
            "Closed poll in game",
            game_id=self.id,
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
        self.updated_at = datetime.now()
        
        # Save the changes if the game is already in a session
        session = object_session(self)
        if session:
            session.commit()
        
        logger.info(
            "Added vote to poll in game",
            game_id=self.id,
            poll_id=poll_id,
            user_id=user_id,
            option_index=option_index
        ) 