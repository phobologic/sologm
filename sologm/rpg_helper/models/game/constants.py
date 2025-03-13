"""
Constants for game models.
"""
from enum import Enum, IntEnum
from typing import Optional

from sologm.rpg_helper.models.game.errors import GameError

class GameType(str, Enum):
    """Game type enumeration."""
    STANDARD = "standard"
    MYTHIC = "mythic"
    # Add more game types as needed

class MythicChaosFactor(IntEnum):
    """Chaos factor for Mythic GME."""
    MIN = 1
    LOW = 3
    AVERAGE = 5
    HIGH = 7
    MAX = 9

class ChaosBoundaryError(GameError):
    """Exception raised when attempting to set chaos factor outside valid range."""
    def __init__(self, attempted: int, current: Optional[int] = None):
        self.attempted = attempted
        self.current = current
        
        # First check for None
        if attempted is None:
            message = "Invalid chaos factor: cannot be None"
        # Then check for boolean values
        elif isinstance(attempted, bool):
            message = "Invalid chaos factor: boolean values are not allowed"
        # Then check if it's a valid integer
        elif not isinstance(attempted, int):
            message = f"Invalid chaos factor: {attempted} (must be an integer)"
        # Check if it's in the valid range of values (1-9)
        elif attempted not in range(MythicChaosFactor.MIN, MythicChaosFactor.MAX + 1):
            if current is not None:
                if attempted < MythicChaosFactor.MIN:
                    message = f"Cannot decrease chaos factor below minimum ({MythicChaosFactor.MIN}, value provided: {attempted})"
                else:
                    message = f"Cannot increase chaos factor above maximum ({MythicChaosFactor.MAX}, value provided: {attempted})"
            else:
                message = f"Invalid chaos factor: {attempted} (must be between {MythicChaosFactor.MIN} and {MythicChaosFactor.MAX})"
            
        super().__init__(message) 