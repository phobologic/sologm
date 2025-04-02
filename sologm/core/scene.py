"""Scene management functionality."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sologm.storage.file_manager import FileManager
from sologm.utils.errors import SceneError

logger = logging.getLogger(__name__)

@dataclass
class Scene:
    """Represents a scene in a game."""

    id: str
    game_id: str
    title: str
    description: str
    status: str  # active, completed
    sequence: int
    created_at: datetime
    modified_at: datetime


class SceneManager:
    """Manages scene operations."""

    def __init__(self, file_manager: Optional[FileManager] = None):
        """Initialize the scene manager.

        Args:
            file_manager: Optional FileManager instance. If not provided,
                a new one will be created.
        """
        self.file_manager = file_manager or FileManager()

    def create_scene(self, game_id: str, title: str, description: str) -> Scene:
        """Create a new scene in the specified game.

        Args:
            game_id: ID of the game to create the scene in.
            title: Title of the scene.
            description: Description of the scene.

        Returns:
            The created Scene object.

        Raises:
            SceneError: If there's an error creating the scene.
        """
        # Get the game's scenes to determine sequence number
        game_path = self.file_manager.get_game_path(game_id)
        game_data = self.file_manager.read_yaml(game_path / "game.yaml")
        
        if not game_data:
            raise SceneError(f"Game {game_id} not found")
            
        scenes = game_data.get("scenes", [])
        sequence = len(scenes) + 1
        
        # Generate scene ID from title
        scene_id = f"scene-{sequence}-{title.lower().replace(' ', '-')}"
        
        # Create scene data
        now = datetime.utcnow()
        scene = Scene(
            id=scene_id,
            game_id=game_id,
            title=title,
            description=description,
            status="active",
            sequence=sequence,
            created_at=now,
            modified_at=now
        )
        
        # Save scene data
        scene_path = self.file_manager.get_scene_path(game_id, scene_id)
        scene_data = {
            "id": scene.id,
            "game_id": scene.game_id,
            "title": scene.title,
            "description": scene.description,
            "status": scene.status,
            "sequence": scene.sequence,
            "created_at": scene.created_at.isoformat(),
            "modified_at": scene.modified_at.isoformat()
        }
        self.file_manager.write_yaml(scene_path / "scene.yaml", scene_data)
        
        # Update game's scene list
        scenes.append(scene_id)
        game_data["scenes"] = scenes
        self.file_manager.write_yaml(game_path / "game.yaml", game_data)
        
        # Set as active scene
        self.file_manager.set_active_scene_id(game_id, scene_id)
        
        logger.debug(f"Created scene {scene_id} in game {game_id}")
        return scene

    def list_scenes(self, game_id: str) -> List[Scene]:
        """List all scenes for the specified game.

        Args:
            game_id: ID of the game to list scenes for.

        Returns:
            List of Scene objects.

        Raises:
            SceneError: If there's an error listing the scenes.
        """
        game_path = self.file_manager.get_game_path(game_id)
        game_data = self.file_manager.read_yaml(game_path / "game.yaml")
        
        if not game_data:
            raise SceneError(f"Game {game_id} not found")
            
        scenes = []
        for scene_id in game_data.get("scenes", []):
            scene_path = self.file_manager.get_scene_path(game_id, scene_id)
            scene_data = self.file_manager.read_yaml(scene_path / "scene.yaml")
            
            if scene_data:
                scene = Scene(
                    id=scene_data["id"],
                    game_id=scene_data["game_id"],
                    title=scene_data["title"],
                    description=scene_data["description"],
                    status=scene_data["status"],
                    sequence=scene_data["sequence"],
                    created_at=datetime.fromisoformat(scene_data["created_at"]),
                    modified_at=datetime.fromisoformat(scene_data["modified_at"])
                )
                scenes.append(scene)
                
        return sorted(scenes, key=lambda s: s.sequence)

    def get_scene(self, game_id: str, scene_id: str) -> Optional[Scene]:
        """Get a specific scene by ID.

        Args:
            game_id: ID of the game the scene belongs to.
            scene_id: ID of the scene to get.

        Returns:
            Scene object if found, None otherwise.
        """
        scene_path = self.file_manager.get_scene_path(game_id, scene_id)
        scene_data = self.file_manager.read_yaml(scene_path / "scene.yaml")
        
        if scene_data:
            return Scene(
                id=scene_data["id"],
                game_id=scene_data["game_id"],
                title=scene_data["title"],
                description=scene_data["description"],
                status=scene_data["status"],
                sequence=scene_data["sequence"],
                created_at=datetime.fromisoformat(scene_data["created_at"]),
                modified_at=datetime.fromisoformat(scene_data["modified_at"])
            )
        return None

    def get_active_scene(self, game_id: str) -> Optional[Scene]:
        """Get the active scene for the specified game.

        Args:
            game_id: ID of the game to get the active scene for.

        Returns:
            Active Scene object if found, None otherwise.
        """
        active_scene_id = self.file_manager.get_active_scene_id(game_id)
        if active_scene_id:
            return self.get_scene(game_id, active_scene_id)
        return None

    def complete_scene(self, game_id: str, scene_id: str) -> Scene:
        """Mark a scene as complete.

        Args:
            game_id: ID of the game the scene belongs to.
            scene_id: ID of the scene to complete.

        Returns:
            Updated Scene object.

        Raises:
            SceneError: If there's an error completing the scene.
        """
        scene = self.get_scene(game_id, scene_id)
        if not scene:
            raise SceneError(f"Scene {scene_id} not found in game {game_id}")
            
        if scene.status == "completed":
            raise SceneError(f"Scene {scene_id} is already completed")
            
        # Update scene status
        scene.status = "completed"
        scene.modified_at = datetime.utcnow()
        
        # Save updated scene data
        scene_path = self.file_manager.get_scene_path(game_id, scene_id)
        scene_data = {
            "id": scene.id,
            "game_id": scene.game_id,
            "title": scene.title,
            "description": scene.description,
            "status": scene.status,
            "sequence": scene.sequence,
            "created_at": scene.created_at.isoformat(),
            "modified_at": scene.modified_at.isoformat()
        }
        self.file_manager.write_yaml(scene_path / "scene.yaml", scene_data)
        
        # If this was the active scene, try to activate the next scene
        active_scene_id = self.file_manager.get_active_scene_id(game_id)
        if active_scene_id == scene_id:
            scenes = self.list_scenes(game_id)
            next_scenes = [s for s in scenes if s.sequence > scene.sequence and s.status != "completed"]
            if next_scenes:
                self.file_manager.set_active_scene_id(game_id, next_scenes[0].id)
            else:
                self.file_manager.set_active_scene_id(game_id, "")
        
        logger.debug(f"Completed scene {scene_id} in game {game_id}")
        return scene
