from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
import uuid
import json

class GameSettingModel(Base):
    """SQLAlchemy model for game settings as key-value pairs."""
    __tablename__ = 'game_settings'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
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
    
    def __repr__(self):
        return f"<GameSetting(game_id='{self.game_id}', name='{self.name}')>"
    
    @property
    def value(self):
        """Get the typed value of the setting."""
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
            return self.value_str
    
    @value.setter
    def value(self, val):
        """Set the value and determine its type."""
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