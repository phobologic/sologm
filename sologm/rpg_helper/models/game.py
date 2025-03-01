"""
Data models for games and memberships.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set
import uuid


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
    chaos_factor: int = 5  # Current chaos factor (for Mythic GM Emulator)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    members: Set[str] = field(default_factory=set)  # Set of user IDs
    
    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "creator_id": self.creator_id,
            "channel_id": self.channel_id,
            "setting_description": self.setting_description,
            "chaos_factor": self.chaos_factor,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "members": list(self.members)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> 'Game':
        """Create from dictionary."""
        game = cls(
            id=data["id"],
            name=data["name"],
            creator_id=data["creator_id"],
            channel_id=data["channel_id"],
            setting_description=data.get("setting_description"),
            chaos_factor=data.get("chaos_factor", 5)
        )
        
        if "created_at" in data:
            game.created_at = datetime.fromisoformat(data["created_at"])
        
        if "updated_at" in data:
            game.updated_at = datetime.fromisoformat(data["updated_at"])
        
        if "members" in data:
            game.members = set(data["members"])
        
        return game
    
    def add_member(self, user_id: str) -> None:
        """Add a user to the game."""
        self.members.add(user_id)
        self.updated_at = datetime.now()
    
    def remove_member(self, user_id: str) -> bool:
        """
        Remove a user from the game.
        
        Returns:
            bool: True if user was removed, False if user wasn't a member
        """
        if user_id in self.members:
            self.members.remove(user_id)
            self.updated_at = datetime.now()
            return True
        return False
    
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
    
    def update_chaos_factor(self, factor: int) -> None:
        """Update the game's chaos factor."""
        if 1 <= factor <= 9:
            self.chaos_factor = factor
            self.updated_at = datetime.now()


# In-memory storage for games
games_by_id: Dict[str, Game] = {}
games_by_channel: Dict[str, List[Game]] = {}  # Maps channel_id to list of games

def create_game(name: str, creator_id: str, channel_id: str) -> Game:
    """
    Create a new game.
    
    Args:
        name: Name of the game
        creator_id: User ID of the creator
        channel_id: Slack channel ID for the game
        
    Returns:
        Newly created Game object
    """
    game_id = str(uuid.uuid4())
    game = Game(id=game_id, name=name, creator_id=creator_id, channel_id=channel_id)
    game.add_member(creator_id)  # Creator automatically joins
    
    # Store in memory
    games_by_id[game_id] = game
    
    if channel_id not in games_by_channel:
        games_by_channel[channel_id] = []
    games_by_channel[channel_id].append(game)
    
    return game

def get_games_in_channel(channel_id: str) -> List[Game]:
    """
    Get all games in a specific channel.
    
    Args:
        channel_id: Slack channel ID
        
    Returns:
        List of Game objects in the channel
    """
    return games_by_channel.get(channel_id, [])

def get_active_game_for_user(user_id: str, channel_id: str) -> Optional[Game]:
    """
    Get the active game for a user in a channel.
    Currently returns the first game the user is a member of in the channel.
    In the future, this could be expanded to track which game is "active" for the user.
    
    Args:
        user_id: User ID
        channel_id: Slack channel ID
        
    Returns:
        Game object or None if no active game
    """
    channel_games = get_games_in_channel(channel_id)
    for game in channel_games:
        if game.is_member(user_id):
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
    if channel_id in games_by_channel:
        games_by_channel[channel_id] = [g for g in games_by_channel[channel_id] if g.id != game_id]
        if not games_by_channel[channel_id]:
            del games_by_channel[channel_id]
    
    return True