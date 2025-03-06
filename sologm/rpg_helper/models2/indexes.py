"""
Add indexes to the models for better performance.
"""
from sqlalchemy import Index

from sologm.rpg_helper.models2.base import BaseModel
from sologm.rpg_helper.models2.user import User
from sologm.rpg_helper.models2.game.base import Game
from sologm.rpg_helper.models2.scene import Scene
from sologm.rpg_helper.models2.poll import Poll

def create_indexes():
    """Create indexes on the models."""
    # User indexes
    Index('ix_users_username', User.__table__.c.username, unique=True)
    
    # Game indexes
    Index('ix_games_channel_workspace', 
          Game.__table__.c.channel_id, 
          Game.__table__.c.workspace_id, 
          unique=True)
    Index('ix_games_is_active', Game.__table__.c.is_active)
    
    # Scene indexes
    Index('ix_scenes_game_id', Scene.__table__.c.game_id)
    Index('ix_scenes_status', Scene.__table__.c.status)
    Index('ix_scenes_game_status', 
          Scene.__table__.c.game_id, 
          Scene.__table__.c.status)
    
    # Poll indexes
    Index('ix_polls_game_id', Poll.__table__.c.game_id)
    Index('ix_polls_status', Poll.__table__.c.status)
    Index('ix_polls_game_status', 
          Poll.__table__.c.game_id, 
          Poll.__table__.c.status)
    
    # Note: Many-to-many association tables already have indexes on their primary keys 