"""
Mythic Game Master Emulator game model.
"""
from dataclasses import dataclass
from typing import Dict, TYPE_CHECKING

from .base import Game

@dataclass
class MythicGMEGame(Game):
    """
    Represents a game session using the Mythic Game Master Emulator.
    """
    chaos_factor: int = 5  # Mythic GME chaos factor (1-9)
    
    def __post_init__(self):
        """Post-initialization setup."""
        super().__post_init__()
        # Store chaos factor in settings for serialization
        self.settings.mythic_chaos_factor = self.chaos_factor
    
    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        # Add Mythic-specific fields
        data["settings"]["mythic_chaos_factor"] = self.chaos_factor
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> 'MythicGMEGame':
        """Create from dictionary."""
        game = super().from_dict(data)
        
        # Set Mythic-specific fields
        if "settings" in data and "mythic_chaos_factor" in data["settings"]:
            game.chaos_factor = data["settings"]["mythic_chaos_factor"]
        
        return game 