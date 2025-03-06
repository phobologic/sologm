"""
Scene event model.
"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from sologm.rpg_helper.utils.logging import get_logger
from .base import BaseModel

logger = get_logger()

class SceneEvent(BaseModel):
    """
    SQLAlchemy model for scene events.
    
    Represents a single event that occurred in a scene.
    """
    description = Column(Text, nullable=False)
    
    # Foreign key to scene
    scene_id = Column(String(36), ForeignKey('scenes.id'), nullable=False, index=True)
    
    # Relationship back to scene
    scene = relationship("Scene", back_populates="events")
    
    def __init__(self, **kwargs):
        """Initialize a new scene event."""
        super().__init__(**kwargs)
        logger.debug(
            "Created new scene event",
            scene_id=self.scene_id,
            event_id=self.id
        )
    
    def __repr__(self):
        """String representation of the scene event."""
        desc_preview = (self.description[:30] + '...') if len(self.description) > 30 else self.description
        return f"<SceneEvent(id='{self.id}', scene_id='{self.scene_id}', description='{desc_preview}')>"
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        
        # Remove scene_id from the dictionary to avoid circular references
        # when the scene includes its events
        if 'scene_id' in data:
            del data['scene_id']
        
        return data 