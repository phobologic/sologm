"""
Data models for users and their preferences.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Any


@dataclass
class User:
    """
    Represents a user of the RPG Helper bot and their preferences.
    """
    id: str  # Slack user ID
    name: str  # Display name
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # User preferences that apply across all games
    theme: str = "default"  # UI theme preference
    notification_enabled: bool = True  # Whether to receive notifications
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "theme": self.theme,
            "notification_enabled": self.notification_enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create from dictionary."""
        user = cls(
            id=data["id"],
            name=data["name"],
            theme=data.get("theme", "default"),
            notification_enabled=data.get("notification_enabled", True),
        )
        
        if "created_at" in data:
            user.created_at = datetime.fromisoformat(data["created_at"])
        
        if "updated_at" in data:
            user.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return user
    
    def update_theme(self, theme: str) -> None:
        """
        Update the user's theme preference.
        
        Args:
            theme: New theme name
        """
        self.theme = theme
        self.updated_at = datetime.now()
    
    def toggle_notifications(self, enabled: bool) -> None:
        """
        Enable or disable notifications for this user.
        
        Args:
            enabled: Whether notifications should be enabled
        """
        self.notification_enabled = enabled
        self.updated_at = datetime.now()


# In-memory storage for users
users_by_id: Dict[str, User] = {}


def get_user(user_id: str) -> Optional[User]:
    """
    Get a user by ID.
    
    Args:
        user_id: User ID
        
    Returns:
        User object or None if not found
    """
    return users_by_id.get(user_id)


def create_or_update_user(user_id: str, name: str) -> User:
    """
    Create a new user or update an existing one.
    
    Args:
        user_id: User ID
        name: User name
        
    Returns:
        New or updated User object
    """
    if user_id in users_by_id:
        user = users_by_id[user_id]
        if user.name != name:
            user.name = name
            user.updated_at = datetime.now()
        return user
    
    user = User(id=user_id, name=name)
    users_by_id[user_id] = user
    return user


def delete_user(user_id: str) -> bool:
    """
    Delete a user.
    
    Args:
        user_id: User ID
        
    Returns:
        True if deleted, False if not found
    """
    if user_id not in users_by_id:
        return False
    
    del users_by_id[user_id]
    return True