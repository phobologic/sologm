"""
Mythic Game Master Emulator game model.
"""
from dataclasses import dataclass
from typing import Dict, TYPE_CHECKING
from datetime import datetime

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
    
    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        # Add Mythic-specific fields directly to the data dictionary
        data["chaos_factor"] = self.chaos_factor
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> 'MythicGMEGame':
        """Create from dictionary."""
        # Create a copy of the data to avoid modifying the original
        data_copy = dict(data)
        
        # Extract chaos_factor if present
        chaos_factor = data_copy.pop("chaos_factor", 5)
        
        # Create the game instance
        game = super().from_dict(data_copy)
        
        # Set chaos_factor
        game.chaos_factor = chaos_factor
        
        return game 

    def set_chaos(self, chaos_factor: int) -> int:
        """Set the chaos factor.

        Args:
            chaos_factor: The new chaos factor

        Returns:
            The new chaos factor
        
        Raises:
            ValueError: If the current chaos factor is less than or equal to 1 or
              greater than or equal to 9
        """
        if chaos_factor <= 0:
            raise ValueError("Chaos factor cannot be less than or equal to 0")
        if chaos_factor > 9:
            raise ValueError("Chaos factor cannot be greater than 9")
        self.chaos_factor = chaos_factor
        self.updated_at = datetime.now()
        return self.chaos_factor

    def increase_chaos(self) -> int:
        """Increase the chaos factor.

        Returns:
            The new chaos factor
        
        Raises:
            ValueError: If the current chaos factor is greater than or equal to 9
        """
        if self.chaos_factor >= 9:
            raise ValueError("Chaos factor cannot be greater than 9")
        self.chaos_factor += 1
        self.updated_at = datetime.now()
        return self.chaos_factor
            
    def decrease_chaos(self) -> int:
        """Decrease the chaos factor.

        Returns:
            The new chaos factor
        
        Raises:
            ValueError: If the current chaos factor is less than or equal to 1
        """
        if self.chaos_factor <= 1:
            raise ValueError("Chaos factor cannot be less than 1")
        self.chaos_factor -= 1
        self.updated_at = datetime.now()
        return self.chaos_factor