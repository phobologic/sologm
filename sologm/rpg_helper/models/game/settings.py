"""
Game settings model.
"""
from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
import json

from sologm.rpg_helper.utils.logging import get_logger
from sologm.rpg_helper.models.base import BaseModel

logger = get_logger()

class GameSetting(BaseModel):
    """SQLAlchemy model for game settings as key-value pairs."""
    
    name = Column(String(100), nullable=False)
    value_str = Column(Text, nullable=True)
    value_type = Column(String(20), nullable=False)  # 'str', 'int', 'bool', 'float', 'json'
    
    # Foreign key to game
    game_id = Column(String(36), ForeignKey('games.id'), nullable=False, index=True)
    
    # Relationship back to game
    game = relationship("Game", back_populates="settings")
    
    __table_args__ = (
        # Ensure name is unique per game
        UniqueConstraint('game_id', 'name', name='uix_game_setting'),
    )
    
    def __init__(self, **kwargs):
        """Initialize a new game setting."""
        super().__init__(**kwargs)
        logger.debug(
            "Created new game setting",
            game_id=self.game_id,
            name=self.name,
            type=self.value_type
        )
    
    def __repr__(self):
        return f"<GameSetting(game_id='{self.game_id}', name='{self.name}')>"
    
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
            elif self.value_type == 'float':
                return float(self.value_str)
            elif self.value_type == 'json':
                return json.loads(self.value_str)
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
        """Set the value and determine its type."""
        old_type = getattr(self, 'value_type', None)
        old_value = getattr(self, 'value_str', None)
        
        if isinstance(val, str):
            self.value_type = 'str'
            self.value_str = val
        elif isinstance(val, int):
            self.value_type = 'int'
            self.value_str = str(val)
        elif isinstance(val, bool):
            self.value_type = 'bool'
            self.value_str = str(val).lower()
        elif isinstance(val, float):
            self.value_type = 'float'
            self.value_str = str(val)
        elif isinstance(val, (dict, list)):
            self.value_type = 'json'
            self.value_str = json.dumps(val)
        else:
            self.value_type = 'str'
            self.value_str = str(val)
        
        logger.debug(
            "Updated setting value",
            game_id=self.game_id,
            name=self.name,
            old_type=old_type,
            new_type=self.value_type,
            changed=old_value != self.value_str
        )
    
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