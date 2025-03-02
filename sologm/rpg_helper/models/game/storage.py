"""
Storage for game instances.
"""
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Game

# In-memory storage for games
games_by_id: Dict[str, 'Game'] = {}
games_by_channel: Dict[str, 'Game'] = {} 