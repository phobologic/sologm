"""
Data models for games and memberships.
"""
from __future__ import annotations  # This allows forward references in type hints
from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import Dict, List, Optional, Set, Type, Union, Any, Callable, TYPE_CHECKING
import uuid

# Only import Poll when type checking to avoid circular imports
if TYPE_CHECKING:
    from sologm.rpg_helper.models.poll import Poll


class GameError(Exception):
    """Base exception for game-related errors."""
    pass


class ChannelGameExistsError(GameError):
    """Exception raised when attempting to create a game in a channel that already has one."""
    def __init__(self, channel_id: str, existing_game: 'Game'):
        self.channel_id = channel_id
        self.existing_game = existing_game
        super().__init__(f"A game already exists in channel {channel_id}: '{existing_game.name}' (ID: {existing_game.id})")


class SettingValidationError(Exception):
    """Exception raised when a setting value fails validation."""
    def __init__(self, setting_name: str, value: Any, message: str):
        self.setting_name = setting_name
        self.value = value
        self.message = message
        super().__init__(f"Invalid value for setting '{setting_name}': {message}")


@dataclass
class GameSettings:
    """Settings for a game."""
    # Poll settings
    poll_default_timeout_minutes: int = 240
    poll_default_options_count: int = 5
    poll_default_max_votes: int = 1
    poll_allow_multiple_votes_per_option: bool = False
    
    # Define validation rules for each setting
    _validators: Dict[str, Callable[[Any], Optional[str]]] = field(default_factory=dict, repr=False)
    
    def __post_init__(self):
        """Initialize validators for settings."""
        # Define validation functions that return error message or None if valid
        self._validators = {
            "poll_default_timeout_minutes": lambda v: 
                "must be positive" if v <= 0 else None,
                
            "poll_default_options_count": lambda v: 
                "must be at least 2" if v < 2 else None,
                
            "poll_default_max_votes": lambda v: 
                "must be at least 1" if v < 1 else None,
                
            "poll_allow_multiple_votes_per_option": lambda v: 
                "must be a boolean" if not isinstance(v, bool) else None
        }
        
        # Now that validators are set up, validate all initial values
        self.validate_all()
    
    def validate(self, setting_name: str, value: Any) -> None:
        """
        Validate a single setting value.
        
        Args:
            setting_name: Name of the setting to validate
            value: Value to validate
            
        Raises:
            SettingValidationError: If the value is invalid
        """
        # Check if we have a validator for this setting
        if setting_name in self._validators:
            validator = self._validators[setting_name]
            error_message = validator(value)
            
            if error_message:
                raise SettingValidationError(
                    setting_name=setting_name,
                    value=value,
                    message=error_message
                )

    def get_fields(self) -> List[str]:
        """Get a list of all fields."""
        return [f for f in fields(self) if not f.name.startswith('_')]
    
    def validate_all(self) -> None:
        """
        Validate all current settings.
        
        Raises:
            SettingValidationError: If any setting has an invalid value
        """
        # Validate standard fields
        for field_name in [f.name for f in self.get_fields()]:
            value = getattr(self, field_name)
            self.validate(field_name, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {f.name: getattr(self, f.name) for f in self.get_fields()}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameSettings':
        """Create settings from dictionary."""
        # Filter out unknown fields
        known_field_names = {f.name for f in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in known_field_names}
        
        # Create instance with filtered data
        return cls(**filtered_data)
    
    def __setattr__(self, name, value):
        """Handle setting attributes with validation."""
        # During initialization, _validators won't exist yet
        if name == '_validators' or not hasattr(self, '_validators'):
            # Set attribute without validation during initialization
            super().__setattr__(name, value)
            return
        
        # Get list of standard field names
        standard_fields = {f.name for f in fields(self.__class__)}
        
        # If it's a standard field, validate and set normally
        if name in standard_fields:
            # Validate before setting
            if name in self._validators:
                self.validate(name, value)
            super().__setattr__(name, value)
        # If it's not a standard field, raise an error
        else:
            raise AttributeError(f"'GameSettings' has no attribute '{name}'. "
                                f"Only predefined settings are allowed.")


@dataclass
class Game:
    """
    Represents an RPG game session that users can join.
    """
    id: str  # Unique identifier
    name: str  # Game name
    creator_id: str  # User ID of the creator
    channel_id: str  # Slack channel associated with this game
    setting_info: Optional[str] = None  # RPG setting description
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    members: Set[str] = field(default_factory=set)  # Set of user IDs
    settings: GameSettings = field(default_factory=GameSettings)
    polls: List['Poll'] = field(default_factory=list)  # List of polls associated with this game
    
    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "creator_id": self.creator_id,
            "channel_id": self.channel_id,
            "setting_info": self.setting_info,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "members": list(self.members),
            "settings": self.settings.to_dict(),
            "poll_ids": [poll.id for poll in self.polls]  # Store just the IDs for serialization
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> 'Game':
        """Create from dictionary."""
        settings_data = data.get("settings", {})
        
        game = cls(
            id=data["id"],
            name=data["name"],
            creator_id=data["creator_id"],
            channel_id=data["channel_id"],
            setting_info=data.get("setting_info"),
            settings=GameSettings.from_dict(settings_data),
            polls=[]  # Initialize with empty list, we'll resolve poll IDs later
        )
        
        if "created_at" in data:
            game.created_at = datetime.fromisoformat(data["created_at"])
        
        if "updated_at" in data:
            game.updated_at = datetime.fromisoformat(data["updated_at"])
        
        if "members" in data:
            game.members = set(data["members"])
        
        # Store poll IDs temporarily - they'll be resolved to Poll objects when needed
        if "poll_ids" in data:
            game.polls = data["poll_ids"]
        
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
    
    def update_setting_info(self, setting_info: str) -> None:
        """Update the game's setting info."""
        self.setting_info = setting_info
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
        try:
            return getattr(self.settings, key)
        except AttributeError:
            return default
    
    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a game setting value with validation.
        
        Args:
            key: Setting key
            value: Setting value
            
        Raises:
            AttributeError: If the setting doesn't exist
            SettingValidationError: If the value is invalid for this setting
        """
        # This will raise AttributeError if the setting doesn't exist
        setattr(self.settings, key, value)
        self.updated_at = datetime.now()
    
    def delete_setting(self, key: str) -> bool:
        """
        Delete a game setting.
        
        Args:
            key: Setting key
            
        Returns:
            True if setting was deleted
        
        Raises:
            AttributeError: If the setting is a required field or doesn't exist
        """
        # All settings are required fields in this implementation
        raise AttributeError(f"Cannot delete required setting '{key}'")
    
    # Poll settings convenience methods
    def get_poll_default_timeout(self) -> int:
        """Get the default timeout for polls in minutes."""
        return self.settings.poll_default_timeout_minutes
    
    def set_poll_default_timeout(self, minutes: int) -> None:
        """
        Set the default timeout for polls in minutes.
        
        Args:
            minutes: Default poll timeout in minutes (must be positive)
            
        Raises:
            ValueError: If minutes is not positive
        """
        if minutes <= 0:
            raise ValueError(f"Poll timeout must be positive, got {minutes}")
        self.settings.poll_default_timeout_minutes = minutes
        self.updated_at = datetime.now()
    
    def get_poll_default_options_count(self) -> int:
        """Get the default number of options for polls."""
        return self.settings.poll_default_options_count
    
    def set_poll_default_options_count(self, count: int) -> None:
        """
        Set the default number of options for polls.
        
        Args:
            count: Default number of poll options (must be at least 2)
            
        Raises:
            ValueError: If count is less than 2
        """
        if count < 2:
            raise ValueError(f"Poll options count must be at least 2, got {count}")
        self.settings.poll_default_options_count = count
        self.updated_at = datetime.now()
    
    def get_poll_default_max_votes(self) -> int:
        """Get the default maximum votes per user for polls."""
        return self.settings.poll_default_max_votes
    
    def set_poll_default_max_votes(self, max_votes: int) -> None:
        """
        Set the default maximum votes per user for polls.
        
        Args:
            max_votes: Default maximum votes per user (must be at least 1)
            
        Raises:
            ValueError: If max_votes is less than 1
        """
        if max_votes < 1:
            raise ValueError(f"Poll max votes must be at least 1, got {max_votes}")
        self.settings.poll_default_max_votes = max_votes
        self.updated_at = datetime.now()
    
    def get_poll_allow_multiple_votes_per_option(self) -> bool:
        """Get whether polls allow multiple votes for the same option by default."""
        return self.settings.poll_allow_multiple_votes_per_option
    
    def set_poll_allow_multiple_votes_per_option(self, allow: bool) -> None:
        """
        Set whether polls allow multiple votes for the same option by default.
        
        Args:
            allow: Whether multiple votes per option are allowed
        """
        self.settings.poll_allow_multiple_votes_per_option = bool(allow)
        self.updated_at = datetime.now()
    
    def add_poll(self, poll: 'Poll') -> None:
        """
        Add a poll to this game.
        
        Args:
            poll: Poll to add
            
        Raises:
            ValueError: If the poll is already associated with this game
        """
        if poll in self.polls:
            raise ValueError(f"Poll {poll.id} is already associated with this game")
        
        self.polls.append(poll)
        self.updated_at = datetime.now()
    
    def remove_poll(self, poll: 'Poll') -> bool:
        """
        Remove a poll from this game.
        
        Args:
            poll: Poll to remove
            
        Returns:
            True if the poll was removed, False if it wasn't associated with this game
        """
        if poll not in self.polls:
            return False
        
        self.polls.remove(poll)
        self.updated_at = datetime.now()
        return True
    
    def get_polls(self) -> List['Poll']:
        """
        Get all polls associated with this game.
        
        Returns:
            List of Poll objects
        """
        return self.polls

    def resolve_poll_references(self) -> None:
        """
        Resolve poll IDs to Poll objects.
        This should be called after all polls have been loaded.
        """
        from sologm.rpg_helper.models.poll import active_polls, archived_polls
        
        # If polls is already a list of Poll objects, nothing to do
        if not self.polls or (self.polls and isinstance(self.polls[0], str)):
            poll_ids = self.polls
            self.polls = []
            
            for poll_id in poll_ids:
                if poll_id in active_polls:
                    self.polls.append(active_polls[poll_id])
                elif poll_id in archived_polls:
                    self.polls.append(archived_polls[poll_id])


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