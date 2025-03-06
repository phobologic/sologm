"""
Base Game model for the RPG Helper application.
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional, Set, TYPE_CHECKING, Type, ClassVar

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Table, Boolean
from sqlalchemy.orm import relationship, object_session

from sologm.rpg_helper.utils.logging import get_logger
from sologm.rpg_helper.models2.base import BaseModel, get_session, close_session, NotFoundError
from sologm.rpg_helper.models2.game.errors import (
    GameError, ChannelGameExistsError, SceneNotFoundError, PollNotFoundError
)

if TYPE_CHECKING:
    from sologm.rpg_helper.models2.user import User
    from sologm.rpg_helper.models2.scene import Scene
    from sologm.rpg_helper.models2.poll import Poll

logger = get_logger()

# Association table for game-user many-to-many relationship
game_users = Table(
    'game_users',
    BaseModel.metadata,
    Column('game_id', String(36), ForeignKey('games.id'), primary_key=True),
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True)
)

class GameType(str, Enum):
    """Type of game."""
    GENERIC = "generic"
    MYTHIC_GME = "mythic_gme"
    # Add more game types as needed


class Game(BaseModel):
    """
    SQLAlchemy model for games.
    
    Represents a game, which can have multiple scenes, polls, and members.
    """
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    channel_id = Column(String(36), nullable=False, index=True)
    workspace_id = Column(String(36), nullable=False)
    game_type = Column(String(20), nullable=False, default=GameType.GENERIC.value)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    members = relationship("User", secondary=game_users, backref="games")
    scenes = relationship("Scene", back_populates="game", cascade="all, delete-orphan",
                         order_by="Scene.order")
    polls = relationship("Poll", back_populates="game", cascade="all, delete-orphan",
                        order_by="Poll.created_at.desc()")
    settings = relationship("GameSetting", back_populates="game", cascade="all, delete-orphan")
    
    # Class variables for type-specific game classes
    _game_types: ClassVar[Dict[str, Type[Game]]] = {}
    
    def __init__(self, **kwargs):
        """Initialize a new game."""
        super().__init__(**kwargs)
        logger.info(
            "Created new game",
            game_id=self.id,
            name=self.name,
            channel_id=self.channel_id,
            game_type=self.game_type
        )
    
    def __repr__(self):
        """String representation of the game."""
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
        game_type = kwargs.get('game_type', GameType.GENERIC.value)
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
    def get_by_channel(cls, channel_id: str) -> Optional[Game]:
        """
        Get a game by channel ID.
        
        Args:
            channel_id: The channel ID
            
        Returns:
            The game if found, None otherwise
        """
        session = get_session()
        try:
            game = session.query(cls).filter_by(channel_id=channel_id).first()
            
            if game:
                logger.debug(
                    "Found game by channel",
                    channel_id=channel_id,
                    game_id=game.id
                )
                
                # Return the appropriate game type
                if game.game_type in cls._game_types and game.__class__ != cls._game_types[game.game_type]:
                    # Convert to the correct type
                    game_class = cls._game_types[game.game_type]
                    game = session.query(game_class).filter_by(id=game.id).first()
            else:
                logger.debug(
                    "No game found for channel",
                    channel_id=channel_id
                )
            
            return game
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
        from sologm.rpg_helper.models2.game.settings import GameSetting
        
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
        from sologm.rpg_helper.models2.game.settings import GameSetting
        
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