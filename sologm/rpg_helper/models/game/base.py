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
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to settings."""
        if hasattr(self, key):
            return getattr(self, key)
        raise AttributeError(f"No setting named '{key}'")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting with a default value if not found."""
        try:
            return self[key]
        except AttributeError:
            return default
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            key: getattr(self, key)
            for key in self.__annotations__
            if hasattr(self, key)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GameSettings:
        """Create from dictionary."""
        return cls(**{
            key: value
            for key, value in data.items()
            if key in cls.__annotations__
        })

@dataclass
class Game:
    """
    Represents a game session.
    """
    name: str  # Game name
    creator_id: str  # User ID of the creator
    channel_id: str  # Channel ID where the game is being played
    id: str = field(default_factory=lambda: str(uuid.uuid4()))  # Unique identifier with default
    description: str = ""  # Game description
    setting_info: str = ""  # Setting information
    members: Set[str] = field(default_factory=set)  # Set of user IDs of members
    scenes: List[Scene] = field(default_factory=list)  # List of scenes
    current_scene: Optional[Scene] = None  # Current active scene
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    settings: GameSettings = field(default_factory=GameSettings)
    polls: List['Poll'] = field(default_factory=list)  # List of polls
    
    def __post_init__(self):
        """Post-initialization setup."""
        # Add creator to members if not already present
        self.members.add(self.creator_id)
        
        # Create an initial scene if none exist
        if not self.scenes:
            self._create_initial_scene()
        
        logger.debug(
            "Created new game",
            game_id=self.id,
            name=self.name,
            creator_id=self.creator_id,
            channel_id=self.channel_id,
            scene_count=len(self.scenes)
        )
    
    def _create_initial_scene(self):
        """Create an initial scene for the game."""
        scene = self.create_scene()
        
        logger.info(
            "Added initial scene to game",
            game_id=self.id,
            scene_id=scene.id,
            scene_title=scene.title,
            scene_status=scene.status
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of the game
        """
        logger.debug("Converting game to dict", game_id=self.id)
        
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "setting_info": self.setting_info,
            "creator_id": self.creator_id,
            "channel_id": self.channel_id,
            "members": list(self.members),
            "scene_ids": [scene.id for scene in self.scenes],
            "current_scene_id": self.current_scene.id if self.current_scene else None,
            "type": self.__class__.__name__,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "poll_ids": [poll.id for poll in self.polls],
            "settings": self.settings.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], scenes_by_id: Dict[str, Scene] = None, polls_by_id: Dict[str, 'Poll'] = None) -> 'Game':
        """
        Create from dictionary.
        
        Args:
            data: Dictionary data
            scenes_by_id: Dictionary of scenes by ID
            polls_by_id: Dictionary of polls by ID
            
        Returns:
            Game instance
        """
        logger.debug("Creating game from dict", game_id=data["id"])
        
        # Create a copy of the data to avoid modifying the original
        data_copy = dict(data)
        
        # Remove scene and poll IDs from data (we'll handle them separately)
        scene_ids = data_copy.pop("scene_ids", [])
        current_scene_id = data_copy.pop("current_scene_id", None)
        poll_ids = data_copy.pop("poll_ids", [])
        
        # Convert members from list to set
        if "members" in data_copy:
            data_copy["members"] = set(data_copy["members"])
        
        # Create the game instance
        game = cls(**data_copy)
        
        # Set timestamps
        if "created_at" in data:
            game.created_at = datetime.fromisoformat(data["created_at"])
        
        if "updated_at" in data:
            game.updated_at = datetime.fromisoformat(data["updated_at"])
        
        # Add scenes if provided
        if scenes_by_id:
            game.scenes = [scenes_by_id[scene_id] for scene_id in scene_ids if scene_id in scenes_by_id]
            
            # Set current scene
            if current_scene_id and current_scene_id in scenes_by_id:
                game.current_scene = scenes_by_id[current_scene_id]
        
        # Add polls if provided
        if polls_by_id:
            game.polls = [polls_by_id[poll_id] for poll_id in poll_ids if poll_id in polls_by_id]

        # Add settings if provided
        if "settings" in data:
            game.settings = GameSettings.from_dict(data["settings"])
        
        logger.debug(
            "Loaded game data",
            game_id=game.id,
            scene_count=len(game.scenes),
            poll_count=len(game.polls)
        )
        
        return game

    def is_member(self, user_id: str) -> bool:
        """Check if a user is a member of the game.
        
        Args:
            user_id: User ID to check
            
        Returns:
            True if the user is a member, False otherwise
        """
        return user_id in self.members
    
    def add_member(self, user_id: str) -> None:
        """
        Add a member to the game.
        
        Args:
            user_id: User ID to add
        """
        if user_id in self.members:
            raise ValueError(f"User {user_id} is already a member")

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
        Remove a member from the game.
        
        Args:
            user_id: User ID to remove
            
        Returns:
            True if the member was removed, False if not found
        """
        if user_id in self.members:
            self.members.remove(user_id)
            self.updated_at = datetime.now()
            
            logger.debug(
                "Removed member from game",
                game_id=self.id,
                user_id=user_id,
                member_count=len(self.members)
            )
            
            return True
        
        return False
    
    def create_scene(self, title: str = None, description: str = None) -> Scene:
        """
        Create a new scene and add it to the game.
        
        Args:
            title: Scene title
            description: Scene description
            
        Returns:
            The created scene
            
        Raises:
            ValueError: If there is already an active scene
        """
        # Check if there's an active scene
        if self.current_scene and self.current_scene.is_active():
            logger.error(
                "Cannot create new scene while current scene is active",
                game_id=self.id,
                current_scene_id=self.current_scene.id
            )
            raise ValueError("Cannot create new scene while current scene is active")
        
        # Create the scene
        scene = Scene(
            game=self,
            title=title,
            description=description
        )
        
        # Add to scenes list
        self.scenes.append(scene)
        
        # Set as current scene
        self.current_scene = scene
        
        # Update timestamp
        self.updated_at = datetime.now()
        
        logger.info(
            "Created new scene",
            game_id=self.id,
            scene_id=scene.id,
            scene_title=scene.title
        )
        
        return scene
    
    def complete_current_scene(self) -> Optional[Scene]:
        """
        Complete the current scene.
        
        Returns:
            The completed scene, or None if there is no current scene
        """
        if not self.current_scene:
            logger.warning(
                "No current scene to complete",
                game_id=self.id
            )
            return None
        
        # Complete the scene
        self.current_scene.complete()
        
        # Update timestamp
        self.updated_at = datetime.now()
        
        logger.info(
            "Completed scene",
            game_id=self.id,
            scene_id=self.current_scene.id,
            scene_title=self.current_scene.title
        )
        
        return self.current_scene
    
    def abandon_current_scene(self) -> Optional[Scene]:
        """
        Abandon the current scene.
        
        Returns:
            The abandoned scene, or None if there is no current scene
        """
        if not self.current_scene:
            logger.warning(
                "No current scene to abandon",
                game_id=self.id
            )
            return None
        
        # Abandon the scene
        self.current_scene.abandon()
        
        # Update timestamp
        self.updated_at = datetime.now()
        
        logger.info(
            "Abandoned scene",
            game_id=self.id,
            scene_id=self.current_scene.id,
            scene_title=self.current_scene.title
        )
        
        return self.current_scene
    
    def add_poll(self, poll: 'Poll') -> None:
        """
        Add a poll to the game.
        
        Args:
            poll: Poll to add
        """
        self.polls.append(poll)
        self.updated_at = datetime.now()
        
        logger.debug(
            "Added poll to game",
            game_id=self.id,
            poll_id=poll.id,
            poll_count=len(self.polls)
        )
    
    def remove_poll(self, poll_id: str) -> bool:
        """
        Remove a poll from the game.
        
        Args:
            poll_id: ID of the poll to remove
            
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
    
    def get_poll(self, poll_id: str) -> Optional['Poll']:
        """
        Get a poll by ID.
        
        Args:
            poll_id: ID of the poll to get
            
        Returns:
            The poll, or None if not found
        """
        for poll in self.polls:
            if poll.id == poll_id:
                return poll
        
        return None
    
    def get_active_polls(self) -> List['Poll']:
        """
        Get all active polls.
        
        Returns:
            List of active polls
        """
        return [poll for poll in self.polls if not poll.is_closed()]
    
    def get_closed_polls(self) -> List['Poll']:
        """
        Get all closed polls.
        
        Returns:
            List of closed polls
        """
        return [poll for poll in self.polls if poll.is_closed()]
