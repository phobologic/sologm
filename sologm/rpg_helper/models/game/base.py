"""
Base game model.
"""
from __future__ import annotations
from dataclasses import dataclass, field, fields
from datetime import datetime
from typing import Dict, List, Optional, Set, Any, TYPE_CHECKING
import uuid

# Import Scene and SceneStatus for actual use
from ..scene import Scene, SceneStatus

# Only import Poll when type checking to avoid circular imports
if TYPE_CHECKING:
    from ..poll import Poll

from sologm.rpg_helper.utils.logging import get_logger
from .storage import games_by_id, games_by_channel

logger = get_logger()

@dataclass
class GameSettings:
    """Settings for a game."""
    # Scene settings
    scene_default_status: str = "active"
    scene_allow_multiple_active: bool = False
    
    # Poll settings
    poll_default_timeout: int = 60  # seconds
    poll_default_option_count: int = 5
    poll_default_max_votes: int = 1
    poll_allow_multiple_votes_per_option: bool = False
    
    def __getitem__(self, key):
        """Allow dictionary-style access to settings."""
        return getattr(self, key)
    
    def get(self, key, default=None):
        """Get a setting value with a default."""
        return getattr(self, key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            field.name: getattr(self, field.name)
            for field in fields(self)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameSettings':
        """Create from dictionary."""
        # Filter out unknown fields
        known_fields = {field.name for field in fields(cls)}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered_data)

@dataclass
class Game:
    """
    Represents a game session.
    """
    id: str  # Unique identifier
    name: str  # Display name
    creator_id: str  # User ID of the creator
    channel_id: str  # Discord channel ID
    setting_info: Optional[str] = None  # Game setting information
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    members: Set[str] = field(default_factory=set)  # Set of user IDs
    settings: GameSettings = field(default_factory=GameSettings)
    polls: List['Poll'] = field(default_factory=list)  # List of polls
    scenes: List[Scene] = field(default_factory=list)  # List of scenes
    current_scene: Optional[Scene] = None  # Currently active scene
    
    def __post_init__(self):
        """Post-initialization setup."""
        # Always add creator as member
        self.members.add(self.creator_id)
        logger.debug(
            "Created new game",
            game_id=self.id,
            name=self.name,
            creator_id=self.creator_id,
            channel_id=self.channel_id
        )
    
    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary for serialization."""
        logger.debug("Converting game to dict", game_id=self.id)
        
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
            "scene_ids": [scene.id for scene in self.scenes],
            "current_scene_id": self.current_scene.id if self.current_scene else None,
            "type": self.__class__.__name__
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> 'Game':
        """Create from dictionary."""
        logger.debug("Creating game from dict", game_id=data["id"])
        
        # Create the game instance
        game_cls = cls
        if data.get("type") == "MythicGMEGame":
            from .mythic import MythicGMEGame
            game_cls = MythicGMEGame
        
        # Extract basic fields
        game = game_cls(
            id=data["id"],
            name=data["name"],
            creator_id=data["creator_id"],
            channel_id=data["channel_id"],
            setting_info=data.get("setting_info")
        )
        
        # Set timestamps
        if "created_at" in data:
            game.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            game.updated_at = datetime.fromisoformat(data["updated_at"])
        
        # Set members
        if "members" in data:
            game.members = set(data["members"])
        
        # Set settings
        if "settings" in data:
            game.settings = GameSettings.from_dict(data["settings"])
        
        # Scenes will be loaded separately
        
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
        
        logger.debug(
            "Added member to game",
            game_id=self.id,
            user_id=user_id,
            member_count=len(self.members)
        )
    
    def remove_member(self, user_id: str) -> bool:
        """
        Remove a user from the game.
        
        Args:
            user_id: The ID of the user to remove
            
        Returns:
            True if the user was removed, False if they weren't a member
            
        Raises:
            ValueError: If attempting to remove the creator
        """
        if user_id == self.creator_id:
            logger.error(
                "Attempted to remove game creator",
                game_id=self.id,
                creator_id=self.creator_id
            )
            raise ValueError("Cannot remove the game creator")
        
        if user_id not in self.members:
            return False
        
        self.members.remove(user_id)
        self.updated_at = datetime.now()
        
        logger.debug(
            "Removed member from game",
            game_id=self.id,
            user_id=user_id,
            member_count=len(self.members)
        )
        
        return True
    
    def is_member(self, user_id: str) -> bool:
        """
        Check if a user is a member of the game.
        
        Args:
            user_id: The ID of the user to check
            
        Returns:
            True if the user is a member, False otherwise
        """
        return user_id in self.members
    
    def add_poll(self, poll: 'Poll') -> None:
        """
        Add a poll to the game.
        
        Args:
            poll: The poll to add
        """
        self.polls.append(poll)
        self.updated_at = datetime.now()
        
        logger.debug(
            "Added poll to game",
            game_id=self.id,
            poll_id=poll.id,
            poll_count=len(self.polls)
        )
    
    def get_poll(self, poll_id: str) -> Optional['Poll']:
        """
        Get a poll by ID.
        
        Args:
            poll_id: The ID of the poll to get
            
        Returns:
            The poll, or None if not found
        """
        for poll in self.polls:
            if poll.id == poll_id:
                return poll
        return None
    
    def remove_poll(self, poll_id: str) -> bool:
        """
        Remove a poll from the game.
        
        Args:
            poll_id: The ID of the poll to remove
            
        Returns:
            True if the poll was removed, False if not found
        """
        for i, poll in enumerate(self.polls):
            if poll.id == poll_id:
                del self.polls[i]
                self.updated_at = datetime.now()
                
                logger.debug(
                    "Removed poll from game",
                    game_id=self.id,
                    poll_id=poll_id,
                    poll_count=len(self.polls)
                )
                
                return True
        return False
    
    def add_scene(self, scene: Scene) -> None:
        """
        Add a scene to the game.
        
        Args:
            scene: The scene to add
        """
        self.scenes.append(scene)
        self.updated_at = datetime.now()
        
        logger.info(
            "Added scene to game",
            game_id=self.id,
            scene_id=scene.id,
            scene_count=len(self.scenes)
        )
        
        # If this is the first scene, make it the current scene
        if len(self.scenes) == 1:
            self.set_current_scene(scene.id)
    
    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """
        Get a scene by ID.
        
        Args:
            scene_id: The ID of the scene to get
            
        Returns:
            The scene, or None if not found
        """
        for scene in self.scenes:
            if scene.id == scene_id:
                return scene
        return None
    
    def remove_scene(self, scene_id: str) -> bool:
        """
        Remove a scene from the game.
        
        Args:
            scene_id: The ID of the scene to remove
            
        Returns:
            True if the scene was removed, False if not found
        """
        for i, scene in enumerate(self.scenes):
            if scene.id == scene_id:
                # If this is the current scene, clear it
                if self.current_scene and self.current_scene.id == scene_id:
                    self.current_scene = None
                
                del self.scenes[i]
                self.updated_at = datetime.now()
                
                logger.debug(
                    "Removed scene from game",
                    game_id=self.id,
                    scene_id=scene_id,
                    scene_count=len(self.scenes)
                )
                
                return True
        return False
    
    def set_current_scene(self, scene_id: str) -> bool:
        """
        Set the current scene.
        
        Args:
            scene_id: The ID of the scene to set as current
            
        Returns:
            True if the scene was set, False if not found
        """
        scene = self.get_scene(scene_id)
        if not scene:
            logger.error(
                "Attempted to set non-existent scene as current",
                game_id=self.id,
                scene_id=scene_id
            )
            return False
        
        old_scene_id = self.current_scene.id if self.current_scene else None
        self.current_scene = scene
        self.updated_at = datetime.now()
        
        logger.debug(
            "Set current scene",
            game_id=self.id,
            scene_id=scene_id,
            old_scene_id=old_scene_id
        )
        
        return True
    
    def get_active_scenes(self) -> List[Scene]:
        """
        Get all active scenes.
        
        Returns:
            List of active scenes
        """
        return [scene for scene in self.scenes if scene.status == SceneStatus.ACTIVE] 