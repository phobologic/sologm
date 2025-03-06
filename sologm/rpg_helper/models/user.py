"""
User model for the RPG Helper application.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Set

from sqlalchemy import Column, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel, get_session, close_session
from sologm.rpg_helper.utils.logging import get_logger

logger = get_logger()

# Association table for many-to-many relationship between users and games
user_game_association = Table(
    'user_game_association',
    BaseModel.metadata,
    Column('user_id', String(36), ForeignKey('users.id'), primary_key=True),
    Column('game_id', String(36), ForeignKey('games.id'), primary_key=True)
)

class User(BaseModel):
    """
    SQLAlchemy model for users.
    
    Represents a user of the application, typically corresponding to a Slack user.
    """
    username = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    
    # Relationships
    games = relationship("Game", secondary=user_game_association, back_populates="members")
    
    def __init__(self, **kwargs):
        """Initialize a new user."""
        super().__init__(**kwargs)
        logger.debug(
            "Created new user",
            user_id=self.id,
            username=self.username
        )
    
    def __repr__(self) -> str:
        return f"<User(id='{self.id}', username='{self.username}')>"
    
    @classmethod
    def get_by_username(cls, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            username: The username to look up
            
        Returns:
            The user if found, None otherwise
        """
        session = get_session()
        try:
            user = session.query(cls).filter_by(username=username).first()
            if user:
                logger.debug(
                    "Found user by username",
                    username=username,
                    user_id=user.id
                )
            else:
                logger.debug(
                    "User not found by username",
                    username=username
                )
            return user
        finally:
            close_session(session)
    
    @classmethod
    def get_or_create(cls, user_id: str, username: str, **kwargs) -> tuple[User, bool]:
        """
        Get a user by ID, or create if not found.
        
        Args:
            user_id: The ID of the user
            username: The username of the user
            **kwargs: Additional user attributes
            
        Returns:
            Tuple of (user, created) where created is True if a new user was created
        """
        session = get_session()
        try:
            user = session.query(cls).filter_by(id=user_id).first()
            if user is None:
                logger.info(
                    "Creating new user",
                    user_id=user_id,
                    username=username
                )
                user = cls(id=user_id, username=username, **kwargs)
                session.add(user)
                session.commit()
                return user, True
            else:
                logger.debug(
                    "Found existing user",
                    user_id=user_id,
                    username=user.username
                )
                return user, False
        finally:
            close_session(session)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the user to a dictionary.
        
        Returns:
            Dictionary representation of the user
        """
        data = super().to_dict()
        
        # Add game IDs if games are loaded
        if 'games' in self.__dict__:
            data['game_ids'] = [game.id for game in self.games]
            logger.debug(
                "Added game IDs to user dict",
                user_id=self.id,
                game_count=len(self.games)
            )
        
        return data
    
    @property
    def game_count(self) -> int:
        """Get the number of games the user is a member of."""
        count = len(self.games)
        logger.debug(
            "Retrieved user game count",
            user_id=self.id,
            game_count=count
        )
        return count 