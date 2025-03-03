"""
Mythic Game Master Emulator game model.
"""
from dataclasses import dataclass, field
from typing import Dict, TYPE_CHECKING
from datetime import datetime

from .base import Game, GameSettings

@dataclass
class MythicGMEGame(Game):
    """
    Represents a game session using the Mythic Game Master Emulator.
    """
    # Override the settings field with a default that includes Mythic-specific settings
    settings: GameSettings = field(default_factory=lambda: GameSettings(
        mythic_chaos_factor=5  # Default chaos factor
    ))
    
    def __post_init__(self):
        """Post-initialization setup."""
        super().__post_init__()
    
    @property
    def chaos_factor(self) -> int:
        """Get the current chaos factor."""
        return self.settings.mythic_chaos_factor
    
    @chaos_factor.setter
    def chaos_factor(self, value: int) -> None:
        """Set the chaos factor."""
        self.set_chaos(value)
    
    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        # No need to add Mythic-specific fields as they're already in settings
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> 'MythicGMEGame':
        """Create from dictionary."""
        # Create a copy of the data to avoid modifying the original
        data_copy = dict(data)
        
        # Create the game instance
        game = super(MythicGMEGame, cls).from_dict(data_copy)
        
        return game

    def set_chaos(self, chaos_factor: int) -> int:
        """Set the chaos factor.

        Args:
            chaos_factor: The new chaos factor

        Returns:
            The new chaos factor
        
        Raises:
            ValueError: If the chaos factor is less than or equal to 1 or
              greater than 9
        """
        if chaos_factor <= 1:
            raise ValueError("Chaos factor cannot be less than or equal to 1")
        if chaos_factor > 9:
            raise ValueError("Chaos factor cannot be greater than 9")
        
        self.settings.mythic_chaos_factor = chaos_factor
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
        
        self.settings.mythic_chaos_factor += 1
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
        
        self.settings.mythic_chaos_factor -= 1
        self.updated_at = datetime.now()
        return self.chaos_factor