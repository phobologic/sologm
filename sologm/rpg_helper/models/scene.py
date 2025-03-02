"""
Data models for game scenes.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .game import Game


class SceneStatus(Enum):
    """Status of a scene."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class SceneEvent:
    """Represents a single event that occurred in a scene."""
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for serialization."""
        return {
            "description": self.description,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> SceneEvent:
        """Create from dictionary."""
        event = cls(description=data["description"])
        if "timestamp" in data:
            event.timestamp = datetime.fromisoformat(data["timestamp"])
        return event


@dataclass
class Scene:
    """
    Represents a scene in a game.
    """
    id: str  # Unique identifier
    game: Game  # Reference to the game this scene belongs to
    title: Optional[str] = None  # Scene title
    description: Optional[str] = None  # General scene description
    status: SceneStatus = field(default=SceneStatus.ACTIVE)
    events: List[SceneEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    @classmethod
    def create(cls, id: str, title: str, description: str, game: Game) -> 'Scene':
        """
        Create a new full scene.
        
        Args:
            id: Scene ID
            title: Scene title
            description: Scene description
            game: Game this scene belongs to
            
        Returns:
            New Scene instance
        """
        return cls(
            id=id,
            title=title,
            description=description,
            game=game
        )
    
    def add_event(self, description: str) -> SceneEvent:
        """
        Add a new event to the scene.
        
        Args:
            description: Description of what happened
            
        Returns:
            The created SceneEvent
            
        Raises:
            ValueError: If the scene is not active
        """
        if self.status != SceneStatus.ACTIVE:
            raise ValueError(f"Cannot add events to a {self.status.value} scene")
        
        event = SceneEvent(description=description)
        self.events.append(event)
        self.updated_at = datetime.now()
        return event
    
    def set_title(self, title: str) -> None:
        """
        Set or update the scene title.
        
        Args:
            title: New title for the scene
        """
        self.title = title
        self.updated_at = datetime.now()
    
    def set_description(self, description: str) -> None:
        """
        Set or update the scene description.
        
        Args:
            description: New description for the scene
        """
        self.description = description
        self.updated_at = datetime.now()
    
    def clear_title(self) -> None:
        """Remove the scene title."""
        self.title = None
        self.updated_at = datetime.now()
    
    def clear_description(self) -> None:
        """Remove the scene description."""
        self.description = None
        self.updated_at = datetime.now()
    
    def complete(self, title: Optional[str] = None, description: Optional[str] = None) -> None:
        """
        Mark the scene as completed.
        
        Args:
            title: Optional title to set when completing
            description: Optional description to set when completing
            
        Raises:
            ValueError: If the scene is already completed or abandoned
        """
        if self.status != SceneStatus.ACTIVE:
            raise ValueError(f"Cannot complete a {self.status.value} scene")
        
        if title is not None:
            self.set_title(title)
        
        if description is not None:
            self.set_description(description)
        
        self.status = SceneStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def abandon(self) -> None:
        """
        Mark the scene as abandoned.
        
        Raises:
            ValueError: If the scene is already completed or abandoned
        """
        if self.status != SceneStatus.ACTIVE:
            raise ValueError(f"Cannot abandon a {self.status.value} scene")
        
        self.status = SceneStatus.ABANDONED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, object]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "game_id": self.game.id,
            "status": self.status.value,
            "events": [event.to_dict() for event in self.events],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, object], games_by_id: Dict[str, Game]) -> Scene:
        """Create from dictionary."""
        # Look up the game by ID
        game_id = data["game_id"]
        if game_id not in games_by_id:
            raise ValueError(f"Game with ID {game_id} not found")
        
        game = games_by_id[game_id]
        
        scene = cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            game=game,
            status=SceneStatus(data["status"])
        )
        
        if "events" in data:
            scene.events = [SceneEvent.from_dict(event_data) 
                          for event_data in data["events"]]
        
        if "created_at" in data:
            scene.created_at = datetime.fromisoformat(data["created_at"])
        
        if "updated_at" in data:
            scene.updated_at = datetime.fromisoformat(data["updated_at"])
        
        if "completed_at" in data and data["completed_at"]:
            scene.completed_at = datetime.fromisoformat(data["completed_at"])
        
        return scene


# In-memory storage for scenes
scenes_by_id: Dict[str, Scene] = {} 