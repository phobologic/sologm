"""
Game settings model.
"""
from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
import json
from typing import Any, Optional

from sologm.rpg_helper.utils.logging import get_logger
from sologm.rpg_helper.models.base import BaseModel
from sologm.rpg_helper.models.game.errors import SettingTypeChangeError

logger = get_logger()

class GameSetting(BaseModel):
    """SQLAlchemy model for game settings as key-value pairs."""
    
    name = Column(String(100), nullable=False)
    value_str = Column(Text, nullable=False)
    value_type = Column(String(10), nullable=False)
    
    # Foreign key to game
    game_id = Column(String(36), ForeignKey('games.id'), nullable=False, index=True)
    
    # Relationship back to game
    game = relationship("Game", back_populates="settings")
    
    __table_args__ = (
        # Ensure name is unique per game
        UniqueConstraint('game_id', 'name', name='uix_game_setting'),
    )
    
    @staticmethod
    def _determine_value_type_and_str(val: Any) -> tuple[str, str]:
        """
        Determine the type and string representation of a value.
        
        Args:
            val: The value to analyze
            
        Returns:
            Tuple of (value_type, value_str)
            
        Raises:
            ValueError: If val is None
        """
        if val is None:
            raise ValueError("Setting value cannot be None. Use an empty string for unset string values.")
        
        # Determine type and string representation
        if isinstance(val, bool):
            return 'bool', str(val).lower()
        elif isinstance(val, int):
            return 'int', str(val)
        else:
            return 'str', str(val)
    
    def __init__(self, *, game_id: str, name: str, value: Optional[Any] = None, 
                value_str: Optional[str] = None, value_type: Optional[str] = None, **kwargs):
        """
        Initialize a new game setting.
        
        Args:
            game_id: ID of the game this setting belongs to
            name: Name of the setting
            value: Value to set (will determine type automatically)
            value_str: String representation of the value (must be provided with value_type)
            value_type: Type of the value (must be provided with value_str)
            **kwargs: Additional arguments to pass to BaseModel
            
        Raises:
            ValueError: If neither value nor (value_str and value_type) are provided,
                      or if only one of value_str/value_type is provided,
                      or if value is None
        """
        if value is None and (value_str is None or value_type is None):
            raise ValueError(
                "Must provide either value parameter or both value_str and value_type parameters"
            )
        
        if value is not None:
            # Use our type detection logic
            value_type, value_str = self._determine_value_type_and_str(value)
        
        kwargs['value_type'] = value_type
        kwargs['value_str'] = value_str
        kwargs['game_id'] = game_id
        kwargs['name'] = name
        
        super().__init__(**kwargs)
        logger.debug(
            "Created new game setting",
            game_id=self.game_id,
            name=self.name,
            type=self.value_type,
            value_str=self.value_str
        )
    
    def __repr__(self):
        return f"<GameSetting(game_id='{self.game_id}', name='{self.name}', value_type='{self.value_type}', value_str='{self.value_str}')>"
    
    def _set_value(self, val: Any, allow_type_change: bool = False) -> None:
        """
        Internal method to set value with type change control.
        
        Args:
            val: The value to set
            allow_type_change: Whether to allow changing the value's type
            
        Raises:
            ValueError: If val is None
            SettingTypeChangeError: If attempting to change type without permission
        """
        new_type, new_str = self._determine_value_type_and_str(val)
        
        # Check for type change if not allowed
        if not allow_type_change and hasattr(self, 'value_type') and self.value_type != new_type:
            raise SettingTypeChangeError(
                setting_name=self.name,
                current_type=self.value_type,
                new_type=new_type,
                game_id=self.game_id
            )
        
        old_type = getattr(self, 'value_type', None)
        old_value = getattr(self, 'value_str', None)
        
        # Set the new values
        self.value_type = new_type
        self.value_str = new_str
        
        # Log the change
        if allow_type_change and old_type != new_type:
            logger.warning(
                "Setting type changed",
                game_id=self.game_id,
                name=self.name,
                old_type=old_type,
                new_type=new_type,
                old_value=old_value,
                new_value=self.value_str
            )
        else:
            logger.debug(
                "Updated setting value",
                game_id=self.game_id,
                name=self.name,
                type=new_type,
                changed=old_value != self.value_str
            )

    @property
    def value(self):
        """Get the typed value of the setting."""
        try:
            if self.value_type == 'str':
                return self.value_str
            elif self.value_type == 'int':
                return int(self.value_str)
            elif self.value_type == 'bool':
                return self.value_str.lower() == 'true'
            else:
                logger.warning(
                    "Unknown value type for setting",
                    game_id=self.game_id,
                    name=self.name,
                    type=self.value_type
                )
                return self.value_str
        except Exception as e:
            logger.error(
                "Error converting setting value",
                game_id=self.game_id,
                name=self.name,
                type=self.value_type,
                error=str(e)
            )
            return self.value_str
    
    @value.setter
    def value(self, val):
        """
        Set the value, maintaining current type.
        
        Args:
            val: The value to set
            
        Raises:
            ValueError: If val is None
            SettingTypeChangeError: If val would change the setting's type
        """
        self._set_value(val, allow_type_change=False)
    
    def reset_value(self, val: Any) -> None:
        """
        Reset the setting value, allowing type change.
        
        Use this method when you explicitly want to change the setting's type.
        
        Args:
            val: The new value to set
            
        Raises:
            ValueError: If val is None
        """
        self._set_value(val, allow_type_change=True)

    @classmethod
    def get_for_game(cls, game_id: str, name: str = None):
        """
        Get settings for a game.
        
        Args:
            game_id: ID of the game
            name: Optional setting name to filter by
            
        Returns:
            List of settings or a single setting if name is provided
            
        Raises:
            NotFoundError: If the game doesn't exist and name is provided
        """
        from sologm.rpg_helper.db.config import get_session, close_session
        from sologm.rpg_helper.models.base import NotFoundError
        
        # First check if the game exists
        session = get_session()
        try:
            # Check if game exists
            from sologm.rpg_helper.models.game.base import Game
            game_exists = session.query(Game).filter_by(id=game_id).first() is not None
            
            if not game_exists:
                logger.warning(
                    "Attempted to get settings for non-existent game",
                    game_id=game_id
                )
                if name:
                    raise NotFoundError(f"Game with ID {game_id} not found")
                return []
            
            # Game exists, proceed with query
            query = session.query(cls).filter_by(game_id=game_id)
            
            if name:
                setting = query.filter_by(name=name).first()
                logger.debug(
                    "Retrieved game setting",
                    game_id=game_id,
                    name=name,
                    found=setting is not None
                )
                if setting is None:
                    logger.info(
                        "Setting not found for game",
                        game_id=game_id,
                        name=name
                    )
                return setting
            else:
                settings = query.all()
                logger.debug(
                    "Retrieved all game settings",
                    game_id=game_id,
                    count=len(settings)
                )
                return settings
        finally:
            close_session(session)

    def to_dict(self):
        """Convert the setting to a dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'game_id': self.game_id,
            'name': self.name,
            'value_str': self.value_str,
            'value_type': self.value_type,
            'value': self.value
        })
        return base_dict 