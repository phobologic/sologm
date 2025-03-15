"""
Base game model.
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Dict, Any, Optional, TYPE_CHECKING, Union

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Table, Boolean, Enum as SQLAlchemyEnum, UniqueConstraint
from sqlalchemy.orm import relationship, object_session

from sologm.rpg_helper.utils.logging import get_logger
from sologm.rpg_helper.models.base import BaseModel, get_session, close_session
from sologm.rpg_helper.models.game.errors import (
    GameError, ChannelGameExistsError
)
from sologm.rpg_helper.models.game.constants import GameType
from sologm.rpg_helper.models.user import user_game_association

if TYPE_CHECKING:
    from sologm.rpg_helper.models.scene import Scene
    from sologm.rpg_helper.models.poll import Poll
    from sologm.rpg_helper.models.user import User

logger = get_logger()

# Association table for game-user many-to-many relationship
game_users = Table(
    'game_users',
    BaseModel.metadata,
    Column('game_id', String(36), ForeignKey('games.id'), primary_key=True),
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True)
)

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
    def get_by_id(cls, game_id: str) -> Optional[Game]:
        """
        Get a game by ID.
        
        Args:
            game_id: The game ID
            
        Returns:
            The game, or None if not found
        """
        from sologm.rpg_helper.db.config import get_session, close_session
        
        session = get_session()
        try:
            return session.query(cls).filter_by(id=game_id).first()
        finally:
            close_session(session)
    
    @classmethod
    def get_by_channel(cls, channel_id: str, workspace_id: str) -> Optional[Game]:
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
    
    @classmethod
    def create_for_channel(cls, channel_id: str, workspace_id: str, **kwargs) -> Game:
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
        
        # Create the game
        game = cls(**kwargs)
        
        # Save the game
        session = get_session()
        try:
            session.add(game)
            session.commit()
            return game
        finally:
            close_session(session)
    
    @classmethod
    def get_all_active(cls) -> List[Game]:
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'channel_id': self.channel_id,
            'workspace_id': self.workspace_id,
            'game_type': self.game_type.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
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
            default: The default value if the setting doesn't exist
            
        Returns:
            The setting value, or the default if not found
        """
        from sologm.rpg_helper.models.game.settings import GameSetting
        
        # Get existing session or create new one
        session = object_session(self)
        if session is None:
            session = get_session()
            try:
                # Check if the setting exists
                setting = session.query(GameSetting).filter_by(
                    game_id=self.id, name=name
                ).first()
                
                return setting.value if setting else default
            finally:
                close_session(session)
        else:
            # Use existing session
            setting = session.query(GameSetting).filter_by(
                game_id=self.id, name=name
            ).first()
            
            return setting.value if setting else default
    
    def set_setting(self, name: str, value: Any) -> None:
        """
        Set a game setting.
        
        Args:
            name: The setting name
            value: The setting value
            
        Raises:
            ValueError: If value is None
        """
        from sologm.rpg_helper.models.game.settings import GameSetting
        
        # Get existing session or create new one
        session = object_session(self)
        if session is None:
            session = get_session()
            try:
                # Check if the setting exists
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
                        name=name,
                        value=value
                    )
                    session.add(setting)
                    
                    logger.debug(
                        "Created new game setting",
                        game_id=self.id,
                        name=name,
                        value=value
                    )
                
                session.commit()
            finally:
                close_session(session)
        else:
            # Use existing session
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
                    name=name,
                    value=value
                )
                session.add(setting)
                
                logger.debug(
                    "Created new game setting",
                    game_id=self.id,
                    name=name,
                    value=value
                )
            
            session.commit()
    
    def reset_setting(self, name: str, value: Any) -> None:
        """
        Reset a game setting, allowing type change.
        
        Args:
            name: The setting name
            value: The new value
            
        Raises:
            ValueError: If value is None
        """
        from sologm.rpg_helper.models.game.settings import GameSetting
        
        # Get existing session or create new one
        session = object_session(self)
        if session is None:
            session = get_session()
            try:
                # Check if the setting exists
                setting = session.query(GameSetting).filter_by(
                    game_id=self.id, name=name
                ).first()
                
                if setting:
                    # Reset the existing setting
                    old_value = setting.value
                    setting.reset_value(value)
                    
                    logger.debug(
                        "Reset game setting",
                        game_id=self.id,
                        name=name,
                        old_value=old_value,
                        new_value=value
                    )
                else:
                    # Create a new setting
                    setting = GameSetting(
                        game_id=self.id,
                        name=name,
                        value=value
                    )
                    session.add(setting)
                    
                    logger.debug(
                        "Created new game setting",
                        game_id=self.id,
                        name=name,
                        value=value
                    )
                
                session.commit()
            finally:
                close_session(session)
        else:
            # Use existing session
            setting = session.query(GameSetting).filter_by(
                game_id=self.id, name=name
            ).first()
            
            if setting:
                # Reset the existing setting
                old_value = setting.value
                setting.reset_value(value)
                
                logger.debug(
                    "Reset game setting",
                    game_id=self.id,
                    name=name,
                    old_value=old_value,
                    new_value=value
                )
            else:
                # Create a new setting
                setting = GameSetting(
                    game_id=self.id,
                    name=name,
                    value=value
                )
                session.add(setting)
                
                logger.debug(
                    "Created new game setting",
                    game_id=self.id,
                    name=name,
                    value=value
                )
            
            session.commit()
    
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