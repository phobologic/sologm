"""
Data models for games and memberships.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Type, Union, Any
import uuid


class GameError(Exception):
    """Base exception for game-related errors."""
    pass


class ChannelGameExistsError(GameError):
    """Exception raised when attempting to create a game in a channel that already has one."""
    def __init__(self, channel_id: str, existing_game: 'Game'):
        self.channel_id = channel_id
        self.existing_game = existing_game
        super().__init__(f"A game already exists in channel {channel_id}: '{existing_game.name}' (ID: {existing_game.id})")


@dataclass
class Game:
    """
    Represents an RPG game session that users can join.
    """
    id: str  # Unique identifier
    name: str  # Game name
    creator_id: str  # User ID of the creator
    channel_id: str  # Slack channel associated with this game
    setting_description: Optional[str] = None  # RPG setting description
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    members: Set[str] = field(default_factory=set)  # Set of user IDs
    settings: Dict[str, Any] = field(default_factory=dict)  # Game settings
    
    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "creator_id": self.creator_id,
            "channel_id": self.channel_id,
            "setting_description": self.setting_description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "members": list(self.members),
            "settings": self.settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> 'Game':
        """Create from dictionary."""
        game = cls(
            id=data["id"],
            name=data["name"],
            creator_id=data["creator_id"],
            channel_id=data["channel_id"],
            setting_description=data.get("setting_description")
        )
        
        if "created_at" in data:
            game.created_at = datetime.fromisoformat(data["created_at"])
        
        if "updated_at" in data:
            game.updated_at = datetime.fromisoformat(data["updated_at"])
        
        if "members" in data:
            game.members = set(data["members"])
        
        if "settings" in data:
            game.settings = data["settings"]
        
        return game
    
    def add_member(self, user_id: str) -> None:
        """
        Add a user to the game.
        
        Args:
            user_id: The ID of the user to add
            
        Raises:
            ValueError: If the user is already a member of the game
        """
        if user_id in self.members:
            raise ValueError(f"User {user_id} is already a member of this game")
        
        self.members.add(user_id)
        self.updated_at = datetime.now()
    
    def remove_member(self, user_id: str) -> bool:
        """
        Remove a user from the game.
        
        Args:
            user_id: The ID of the user to remove
            
        Returns:
            bool: True if user was successfully removed
            
        Raises:
            ValueError: If the user is not a member of the game
        """
        self.members.remove(user_id)
        self.updated_at = datetime.now()
        return True
    
    def is_member(self, user_id: str) -> bool:
        """Check if a user is a member of this game."""
        return user_id in self.members
    
    def is_creator(self, user_id: str) -> bool:
        """Check if a user is the creator of this game."""
        return user_id == self.creator_id
    
    def update_setting(self, description: str) -> None:
        """Update the game's setting description."""
        self.setting_description = description
        self.updated_at = datetime.now()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a game setting value.
        
        Args:
            key: Setting key
            default: Default value if setting doesn't exist
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a game setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self.settings[key] = value
        self.updated_at = datetime.now()
    
    def delete_setting(self, key: str) -> bool:
        """
        Delete a game setting.
        
        Args:
            key: Setting key
            
        Returns:
            True if setting was deleted, False if it didn't exist
        """
        if key in self.settings:
            del self.settings[key]
            self.updated_at = datetime.now()
            return True
        return False


@dataclass
class MythicGMEGame(Game):
    """
    Represents an RPG game session using the Mythic GME system.
    """
    chaos_factor: int = 5  # Current chaos factor (for Mythic GM Emulator)
    
    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary for serialization."""
        data = super().to_dict()
        data["chaos_factor"] = self.chaos_factor
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> 'MythicGMEGame':
        """Create from dictionary."""
        game = super().from_dict(data)
        game.chaos_factor = data.get("chaos_factor", 5)
        return game
    
    def update_chaos_factor(self, factor: int) -> int:
        """
        Update the game's chaos factor.
        
        Args:
            factor: New chaos factor value (must be between 1 and 9)
            
        Returns:
            int: The new chaos factor value
            
        Raises:
            ValueError: If the chaos factor is outside the valid range (1-9)
        """
        if 1 <= factor <= 9:
            self.chaos_factor = factor
            self.updated_at = datetime.now()
            return self.chaos_factor
        else:
            raise ValueError(f"Chaos factor must be between 1 and 9, got {factor}")
    
    def get_chaos_factor(self) -> int:
        """
        Get the current chaos factor.
        
        Returns:
            int: The current chaos factor value

        Raises:
            ValueError: If the chaos factor is outside the valid range (1-9)
        """
        return self.chaos_factor
    
    def increment_chaos_factor(self) -> int:
        """
        Increment the chaos factor by 1.
        
        Returns:
            int: The new chaos factor value if incremented

        Raises:
            ValueError: If the chaos factor is outside the valid range (1-9)
        """
        current_factor = self.get_chaos_factor()
        if current_factor < 9:
            new_factor = current_factor + 1
            return self.update_chaos_factor(new_factor)
    
    def decrement_chaos_factor(self) -> int:
        """
        Decrement the chaos factor by 1.
        
        Returns:
            int: The new chaos factor value if decremented
        """
        current_factor = self.get_chaos_factor()
        if current_factor > 1:
            new_factor = current_factor - 1
            return self.update_chaos_factor(new_factor)

# In-memory storage for games
games_by_id: Dict[str, Game] = {}
games_by_channel: Dict[str, Game] = {}  # Maps channel_id to a single game

# Game type registry for a more extensible approach
GAME_TYPES = {
    "standard": Game,
    "mythic": MythicGMEGame,
    # Add more game types here as they are created
}

def get_game_class(game_type: Optional[str] = None) -> Type[Game]:
    """
    Get the game class for a given game type.
    
    Args:
        game_type: Type of game to create (must be a key in GAME_TYPES)
                  If None, returns the standard Game class
    
    Returns:
        Game class corresponding to the specified type
        
    Raises:
        ValueError: If an invalid game type is specified
    """
    if game_type is None:
        return GAME_TYPES["standard"]

    try:
        return GAME_TYPES[game_type]
    except KeyError:
        valid_types = ", ".join(GAME_TYPES.keys())
        raise ValueError(f"Invalid game type: {game_type}. Valid types are: {valid_types}")

def create_game(
    name: str, 
    creator_id: str, 
    channel_id: str, 
    game_type: Optional[str] = None,
    **kwargs
) -> Game:
    """
    Create a new game for a channel.
    
    Args:
        name: Name of the game
        creator_id: User ID of the creator
        channel_id: Slack channel ID for the game
        game_type: Type of game to create ("standard", "mythic", etc.)
        **kwargs: Additional arguments for specific game types
        
    Returns:
        Newly created Game object
        
    Raises:
        ChannelGameExistsError: If a game already exists in the specified channel
        ValueError: If an invalid game type is specified
    """
    # Check if a game already exists in this channel
    if channel_id in games_by_channel:
        existing_game = games_by_channel[channel_id]
        raise ChannelGameExistsError(channel_id, existing_game)
    
    game_id = str(uuid.uuid4())
    game_class = get_game_class(game_type)
    # Create the appropriate game type
    game = game_class(id=game_id, name=name, creator_id=creator_id, channel_id=channel_id, **kwargs)
    
    game.add_member(creator_id)  # Creator automatically joins
    
    # Store in memory
    games_by_id[game_id] = game
    games_by_channel[channel_id] = game
    
    return game

def get_game_in_channel(channel_id: str) -> Optional[Game]:
    """
    Get the game in a specific channel.
    
    Args:
        channel_id: Slack channel ID
        
    Returns:
        Game object or None if no game exists in the channel
    """
    return games_by_channel.get(channel_id)

def get_active_game_for_user(user_id: str, channel_id: str) -> Optional[Game]:
    """
    Get the active game for a user in a channel.
    The user must be a member of the game.
    
    Args:
        user_id: User ID
        channel_id: Slack channel ID
        
    Returns:
        Game object or None if no active game or user is not a member
    """
    game = get_game_in_channel(channel_id)
    if game and game.is_member(user_id):
        return game
    return None

def delete_game(game_id: str) -> bool:
    """
    Delete a game.
    
    Args:
        game_id: Game ID
        
    Returns:
        True if deleted, False if not found
    """
    if game_id not in games_by_id:
        return False
    
    game = games_by_id[game_id]
    channel_id = game.channel_id
    
    # Remove from games_by_id
    del games_by_id[game_id]
    
    # Remove from games_by_channel
    if channel_id in games_by_channel and games_by_channel[channel_id].id == game_id:
        del games_by_channel[channel_id]
    
    return True