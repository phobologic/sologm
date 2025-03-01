"""
Data models for user preferences.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class UserPreferences:
    """
    User preferences for the RPG Helper.
    """
    user_id: str
    num_options: int = 5  # Number of interpretation options
    timeout_hours: int = 4  # Poll timeout in hours
    active_game_id: Optional[str] = None  # Currently active game for this user
    
    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "num_options": self.num_options,
            "timeout_hours": self.timeout_hours,
            "active_game_id": self.active_game_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> 'UserPreferences':
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            num_options=data.get("num_options", 5),
            timeout_hours=data.get("timeout_hours", 4),
            active_game_id=data.get("active_game_id")
        )


# In-memory storage for user preferences
user_preferences: Dict[str, UserPreferences] = {}

def get_user_preferences(user_id: str) -> UserPreferences:
    """
    Get user preferences, creating default preferences if none exist.
    
    Args:
        user_id: User ID
        
    Returns:
        UserPreferences object
    """
    if user_id not in user_preferences:
        user_preferences[user_id] = UserPreferences(user_id)
    
    return user_preferences[user_id]